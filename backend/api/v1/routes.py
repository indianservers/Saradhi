import asyncio
import base64
import csv
import hashlib
import hmac
import io
import json
from datetime import datetime, timedelta
from decimal import Decimal
from time import perf_counter
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import aliased

from ai_platform.gateway import agents as AI_AGENTS
from ai_platform.inference import service as ai_service
from ai_platform.optimization.dispatch.greedy import greedy_one_to_one
from backend.api.v1 import schemas as s
from backend.api.v1.dependencies import DB, Actor
from backend.application import (
    ai_agents,
    city_launch,
    commerce,
    finance,
    identity,
    logistics,
    razorpay_payments,
    recurring,
)
from backend.application.common import add, audit, branch_scope, event, now, owned, scoped
from backend.domain.rules import BusinessError, money
from backend.integrations.payments.razorpay import RazorpayGateway
from backend.modules.bulk_data import service as bulk_data
from backend.modules.customer_admin import service as customer_admin
from backend.modules.fulfillment import eta as eta_engine
from backend.modules.tracking import service as tracking
from backend.modules.tracking.realtime import publish
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository
from backend.shared.client_ip import client_ip

router = APIRouter(prefix="/api/v1")
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]
Limit = Annotated[int, Query(ge=1, le=100)]
CatalogBranchName = Annotated[str | None, Query(max_length=100)]
CatalogMaxPrice = Annotated[Decimal | None, Query(gt=0, max_digits=12, decimal_places=4)]
CatalogDietary = Annotated[list[str] | None, Query(max_length=6)]


def decode_cursor(raw):
    if raw is None:
        return None
    try:
        return UUID(bytes=base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
    except (ValueError, TypeError) as exc:
        raise BusinessError("invalid_cursor", "Invalid page cursor", 422) from exc


async def page(db, model, predicates, out, cursor, limit):
    rows, next_id = await Repository(db).page(
        model, predicates, after=decode_cursor(cursor), limit=limit
    )
    return {
        "items": [out.model_validate(row) for row in rows],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


def local_auth(request):
    verifier = request.app.state.token_verifier
    if not isinstance(verifier, identity.LocalTokenVerifier):
        raise BusinessError(
            "local_auth_unconfigured",
            "Configure AUTH_PRIVATE_KEY_PATH for password authentication",
            503,
        )
    return verifier


async def auth_budget(request, identity_key, endpoint="auth"):
    # Separate committed transaction preserves failed login/OTP rate counters.
    async with request.app.state.sessions.begin() as db:
        allowed = await identity.rate_limit(
            db,
            identity_key,
            client_ip(request),
            limit=request.app.state.settings.auth_rate_limit_per_minute,
            endpoint=endpoint,
        )
    if not allowed:
        raise BusinessError(
            "rate_limited", "Authentication rate limit exceeded; retry after 60 seconds", 429
        )


async def actor_budget(request, actor, endpoint, limit):
    """Committed shared endpoint + user/IP throttle for costly or sensitive actions."""
    async with request.app.state.sessions.begin() as rate_db:
        allowed = await identity.rate_limit(
            rate_db,
            actor.subject,
            client_ip(request),
            limit=limit,
            endpoint=endpoint,
        )
    if not allowed:
        raise BusinessError(
            "rate_limited", "Action rate limit exceeded; retry after 60 seconds", 429
        )


@router.post("/auth/register", response_model=s.IdOut, status_code=201, tags=["Identity"])
async def register(body: s.RegisterIn, request: Request):
    local_auth(request)
    await auth_budget(request, body.email.lower(), "register")
    async with request.app.state.sessions.begin() as db:
        return await identity.register(db, body.email, body.password.get_secret_value())


@router.post("/auth/login", response_model=s.TokenOut, tags=["Identity"])
async def login(body: s.LoginIn, request: Request):
    verifier = local_auth(request)
    await auth_budget(request, body.email.lower(), "login")
    async with request.app.state.sessions.begin() as db:
        result = await identity.login(db, verifier, body.email, body.password.get_secret_value())
    if result is None:
        raise BusinessError("invalid_credentials", "Invalid credentials", 401)
    return result


@router.post("/auth/refresh", response_model=s.TokenOut, tags=["Identity"])
async def refresh(body: s.RefreshIn, request: Request):
    verifier = local_auth(request)
    await auth_budget(
        request,
        "refresh:" + identity.digest(body.refresh_token.get_secret_value()),
        "refresh",
    )
    async with request.app.state.sessions.begin() as db:
        result = await identity.refresh(db, verifier, body.refresh_token.get_secret_value())
    if result is None:
        raise BusinessError("invalid_refresh", "Refresh token is invalid or reused", 401)
    return result


@router.post("/auth/logout", status_code=204, tags=["Identity"])
async def logout(body: s.RefreshIn, actor: Actor, db: DB):
    token = await db.scalar(
        select(m.RefreshToken).where(
            m.RefreshToken.digest == identity.digest(body.refresh_token.get_secret_value())
        )
    )
    if token:
        record = await Repository(db).require(m.Session, token.session_id, lock=True)
        owned(actor, record.user_id)
        record.revoked_at = now()
    return Response(status_code=204)


@router.get("/roles", response_model=s.Page[s.NamedOut], tags=["Identity"])
async def roles(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(db, m.Role, [], s.NamedOut, cursor, limit)


@router.get("/memberships", response_model=s.Page[s.IdOut], tags=["Identity"])
async def memberships(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(
        db, m.Membership, [m.Membership.user_id == UUID(actor.subject)], s.IdOut, cursor, limit
    )


async def _require_customer_account(db, actor):
    user_id = UUID(actor.subject)
    is_customer = await db.scalar(
        select(m.RoleAssignment.id)
        .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
        .where(m.RoleAssignment.user_id == user_id, m.Role.name == "customer")
        .limit(1)
    )
    if not is_customer:
        raise BusinessError("forbidden", "Customer account required", 403)
    return user_id


@router.get("/me/consents", tags=["Customer privacy"])
async def customer_consent_state(actor: Actor, db: DB):
    user_id = await _require_customer_account(db, actor)
    events = (
        await db.scalars(
            select(m.CustomerConsentEvent)
            .where(m.CustomerConsentEvent.user_id == user_id)
            .order_by(m.CustomerConsentEvent.created_at.desc(), m.CustomerConsentEvent.id.desc())
            .limit(100)
        )
    ).all()
    latest = {}
    for event_row in events:
        key = (event_row.purpose, event_row.channel)
        latest.setdefault(
            key,
            {
                "purpose": event_row.purpose,
                "channel": event_row.channel,
                "enabled": event_row.enabled,
                "policy_version": event_row.policy_version,
                "recorded_at": event_row.created_at.isoformat(),
            },
        )
    return {"items": list(latest.values())}


@router.post("/me/consents", tags=["Customer privacy"])
async def record_customer_consent(body: s.CustomerConsentIn, key: Key, actor: Actor, db: DB):
    user_id = await _require_customer_account(db, actor)
    existing = await db.scalar(
        select(m.CustomerConsentEvent).where(m.CustomerConsentEvent.idempotency_key == key)
    )
    if existing:
        if existing.user_id != user_id:
            raise BusinessError("idempotency_conflict", "Idempotency key already used", 409)
        return {"id": str(existing.id), "enabled": existing.enabled, "replayed": True}
    if body.enabled and body.channel == "email":
        verified = await db.scalar(
            select(m.Email.id).where(m.Email.user_id == user_id, m.Email.verified_at.is_not(None))
        )
        if not verified:
            raise BusinessError("verified_contact_required", "Verify email before opting in", 409)
    if body.enabled and body.channel in {"sms", "whatsapp"}:
        phone = F["identity.user_phone_numbers"]
        verified = await db.scalar(
            select(phone.id)
            .where(phone.user_id == user_id, phone.verified_at.is_not(None))
            .limit(1)
        )
        if not verified:
            raise BusinessError("verified_contact_required", "Verify phone before opting in", 409)
    row = await add(
        db,
        m.CustomerConsentEvent,
        user_id=user_id,
        purpose=body.purpose,
        channel=body.channel,
        enabled=body.enabled,
        policy_version=body.policy_version,
        source="authenticated_customer_api",
        idempotency_key=key,
    )
    return {"id": str(row.id), "enabled": row.enabled, "replayed": False}


@router.post("/auth/challenges", response_model=s.IdOut, status_code=201, tags=["Identity"])
async def challenge(body: s.OtpIn, actor: Actor, request: Request, db: DB):
    email = await db.scalar(select(m.Email.address).where(m.Email.user_id == UUID(actor.subject)))
    await auth_budget(request, "otp-create:" + actor.subject, "otp-create")
    return await identity.create_challenge(
        db,
        UUID(actor.subject),
        body.purpose,
        email,
        request.app.state.settings.otp_pepper.get_secret_value(),
        getattr(request.app.state, "otp_provider", None),
    )


@router.post("/auth/challenges/{challenge_id}/consume", status_code=204, tags=["Identity"])
async def consume_challenge(
    challenge_id: UUID, body: s.OtpConsumeIn, actor: Actor, request: Request
):
    await auth_budget(request, "otp:" + actor.subject, "otp-consume")
    async with request.app.state.sessions.begin() as db:
        valid = await identity.consume_challenge(
            db,
            actor,
            challenge_id,
            body.code.get_secret_value(),
            request.app.state.settings.otp_pepper.get_secret_value(),
        )
    if not valid:
        raise BusinessError("invalid_otp", "Code is invalid, expired or consumed", 401)
    return Response(status_code=204)


@router.post("/organizations", response_model=s.NamedOut, status_code=201, tags=["Merchants"])
async def organization(body: s.NameIn, actor: Actor, db: DB):
    org = await add(db, m.Organization, name=body.name, owner_id=UUID(actor.subject))
    await add(
        db, m.Membership, organization_id=org.id, user_id=UUID(actor.subject), status="active"
    )
    role = await db.scalar(select(m.Role).where(m.Role.name == "merchant_owner"))
    if role is None:
        raise BusinessError(
            "roles_uninitialized", "Apply foundation migrations before onboarding", 503
        )
    await add(
        db, m.RoleAssignment, user_id=UUID(actor.subject), organization_id=org.id, role_id=role.id
    )
    await add(
        db,
        F["merchant.merchant_organizations"],
        organization_id=org.id,
        onboarding_status="pending",
    )
    return org


@router.post(
    "/merchant/onboarding",
    response_model=s.BranchOut,
    status_code=201,
    tags=["Merchant workspace"],
)
async def merchant_onboarding(body: s.MerchantOnboardingIn, actor: Actor, db: DB):
    """Atomically create the initial merchant organization/brand/branch submission."""
    if (body.organization_id is None) == (body.organization_name is None):
        raise BusinessError(
            "organization_selection",
            "Provide an existing authorized organization or a new organization name",
            422,
        )
    if body.organization_id:
        await scoped(db, actor, "merchant.write", body.organization_id)
        organization_id = body.organization_id
    else:
        org = await add(
            db,
            m.Organization,
            name=body.organization_name,
            owner_id=UUID(actor.subject),
        )
        organization_id = org.id
        await add(
            db,
            m.Membership,
            organization_id=org.id,
            user_id=UUID(actor.subject),
            status="active",
        )
        role = await db.scalar(select(m.Role).where(m.Role.name == "merchant_owner"))
        if role is None:
            raise BusinessError("roles_uninitialized", "Apply foundation migrations first", 503)
        await add(
            db,
            m.RoleAssignment,
            user_id=UUID(actor.subject),
            organization_id=org.id,
            role_id=role.id,
        )
        await add(
            db,
            F["merchant.merchant_organizations"],
            organization_id=org.id,
            onboarding_status="pending",
        )
    city = await Repository(db).require(m.City, body.city_id)
    if not city.active:
        raise BusinessError("inactive_city", "Choose an active operating city", 422)
    brand = await add(
        db,
        m.Brand,
        organization_id=organization_id,
        name=body.brand_name,
        merchant_type=body.merchant_type,
    )
    branch = await add(
        db,
        m.Branch,
        brand_id=brand.id,
        organization_id=organization_id,
        city_id=city.id,
        name=body.branch_name,
        latitude=body.latitude,
        longitude=body.longitude,
        status="pending",
        accepting_orders=False,
        version=1,
    )
    return s.BranchOut.model_validate(branch).model_copy(
        update={"merchant_type": brand.merchant_type}
    )


@router.post(
    "/organizations/{organization_id}/members",
    response_model=s.IdOut,
    status_code=201,
    tags=["Identity"],
)
async def member(organization_id: UUID, body: s.MemberIn, actor: Actor, request: Request, db: DB):
    branch = await branch_scope(db, actor, body.branch_id, "organization.members")
    if branch.organization_id != organization_id:
        raise BusinessError("forbidden", "Branch is outside this organization", 403)
    target_user = await Repository(db).require(m.User, body.user_id)
    if target_user.status != "active":
        raise BusinessError("member_inactive", "Only active users can be assigned", 422)
    membership = await db.scalar(
        select(m.Membership).where(
            m.Membership.organization_id == organization_id, m.Membership.user_id == body.user_id
        )
    )
    if membership is None:
        membership = await add(
            db, m.Membership, organization_id=organization_id, user_id=body.user_id, status="active"
        )
    role = await db.scalar(select(m.Role).where(m.Role.name == body.role))
    if role is None:
        raise BusinessError("role_unavailable", "Requested member role is unavailable", 422)
    await add(
        db,
        m.RoleAssignment,
        organization_id=organization_id,
        user_id=body.user_id,
        role_id=role.id,
        branch_id=branch.id,
        city_id=branch.city_id,
    )
    await audit(
        db,
        actor,
        "organization.member_role_assigned",
        body.user_id,
        request.state.request_id,
        organization_id=organization_id,
        current=body.role,
        decision="assigned",
    )
    return membership


@router.post("/geo/countries", response_model=s.CountryOut, status_code=201, tags=["Geography"])
async def create_country(body: s.CountryIn, actor: Actor, db: DB):
    await scoped(db, actor, "geo.write")
    return await add(db, m.Country, **body.model_dump())


@router.get("/geo/countries", response_model=s.Page[s.CountryOut], tags=["Geography"])
async def countries(db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(db, m.Country, [], s.CountryOut, cursor, limit)


@router.post("/geo/cities", response_model=s.CityOut, status_code=201, tags=["Geography"])
async def city(body: s.CityIn, actor: Actor, request: Request, db: DB):
    await scoped(db, actor, "geo.write")
    if body.state_province_id:
        state = await Repository(db).require(F["geo.states_provinces"], body.state_province_id)
        if state.country_id != body.country_id:
            raise BusinessError(
                "state_country_mismatch", "State/province belongs to another country", 422
            )
    created = await add(db, m.City, active=False, **body.model_dump())
    await audit(
        db,
        actor,
        "city.create",
        created.id,
        request.state.request_id,
        current="draft",
        version=1,
    )
    return created


@router.get("/geo/cities", response_model=s.Page[s.CityOut], tags=["Geography"])
async def cities(db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(db, m.City, [m.City.active.is_(True)], s.CityOut, cursor, limit)


@router.get(
    "/operations/authorized-cities",
    response_model=s.Page[s.CityOut],
    tags=["Dispatch operations"],
)
async def authorized_cities(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 100):
    user = await db.get(m.User, UUID(actor.subject))
    if not user or user.status != "active":
        raise BusinessError("forbidden", "Access denied", 403)
    assignments = (
        await db.execute(
            select(m.RoleAssignment, m.Role.name)
            .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
            .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
            .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
            .where(
                m.RoleAssignment.user_id == UUID(actor.subject),
                m.Permission.code == "dispatch.write",
            )
        )
    ).all()
    global_scope = any(
        role == "platform_super_admin" and assignment.organization_id is None
        for assignment, role in assignments
    )
    if global_scope:
        return await page(db, m.City, [m.City.active.is_(True)], s.CityOut, cursor, limit)

    candidates = {
        assignment.city_id
        for assignment, _role in assignments
        if assignment.city_id is not None and assignment.branch_id is None
    }
    permitted = set()
    for city_id in candidates:
        try:
            await scoped(db, actor, "dispatch.write", city_id=city_id)
            permitted.add(city_id)
        except BusinessError:
            continue
    return await page(
        db,
        m.City,
        [m.City.active.is_(True), m.City.id.in_(permitted)],
        s.CityOut,
        cursor,
        limit,
    )


@router.post("/geo/zones", response_model=s.NamedOut, status_code=201, tags=["Geography"])
async def zone(body: s.ZoneIn, actor: Actor, db: DB):
    await scoped(db, actor, "geo.write")
    city = await Repository(db).require(m.City, body.city_id)
    if city.active:
        raise BusinessError(
            "city_config_locked", "Suspend the city before adding a new service zone", 409
        )
    return await add(db, m.Zone, active=True, **body.model_dump())


@router.put("/geo/zones/{zone_id}/categories", tags=["City configuration"])
async def set_zone_category(
    zone_id: UUID, body: s.ZoneCategoryIn, actor: Actor, request: Request, db: DB
):
    await scoped(db, actor, "geo.write")
    zone = await Repository(db).require(m.Zone, zone_id)
    city = await Repository(db).require(m.City, zone.city_id)
    if city.active:
        raise BusinessError(
            "city_config_locked", "Suspend the city before changing launch categories", 409
        )
    category = await Repository(db).require(m.Category, body.category_id)
    if category.regulated and body.enabled:
        raise BusinessError(
            "regulated_category_unavailable",
            "Regulated categories require an approved compliance workflow",
            409,
        )
    previous = await db.scalar(
        select(m.ZoneCategory)
        .where(m.ZoneCategory.zone_id == zone.id, m.ZoneCategory.category_id == category.id)
        .with_for_update()
    )
    row = await db.scalar(
        insert(m.ZoneCategory)
        .values(zone_id=zone.id, category_id=category.id, enabled=body.enabled)
        .on_conflict_do_update(
            index_elements=["zone_id", "category_id"], set_={"enabled": body.enabled}
        )
        .returning(m.ZoneCategory)
    )
    await audit(
        db,
        actor,
        "city.zone_category_configure",
        zone.id,
        request.state.request_id,
        previous=("enabled" if previous and previous.enabled else "disabled"),
        current="enabled" if body.enabled else "disabled",
    )
    return {
        "id": row.id,
        "zone_id": zone.id,
        "category_id": category.id,
        "enabled": row.enabled,
    }


@router.get("/operations/cities/{city_id}/readiness", tags=["City configuration"])
async def get_city_readiness(city_id: UUID, actor: Actor, db: DB):
    city = await Repository(db).require(m.City, city_id)
    await scoped(db, actor, "geo.write")
    return await city_launch.readiness(db, city)


@router.post("/operations/cities/{city_id}/activate", tags=["City configuration"])
async def activate_city(city_id: UUID, actor: Actor, request: Request, db: DB):
    await scoped(db, actor, "geo.write")
    return await city_launch.activate(db, actor, city_id, request.state.request_id)


@router.post("/operations/cities/{city_id}/suspend", tags=["City configuration"])
async def suspend_city(city_id: UUID, actor: Actor, request: Request, db: DB):
    await scoped(db, actor, "geo.write")
    return await city_launch.deactivate(db, actor, city_id, request.state.request_id)


@router.post("/addresses", response_model=s.AddressOut, status_code=201, tags=["Geography"])
async def address(body: s.AddressIn, actor: Actor, db: DB):
    return await add(db, m.Address, user_id=UUID(actor.subject), **body.model_dump())


@router.get("/addresses", response_model=s.Page[s.AddressOut], tags=["Geography"])
async def addresses(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(
        db, m.Address, [m.Address.user_id == UUID(actor.subject)], s.AddressOut, cursor, limit
    )


@router.post("/merchants/brands", response_model=s.NamedOut, status_code=201, tags=["Merchants"])
async def brand(body: s.BrandIn, actor: Actor, db: DB):
    await scoped(db, actor, "merchant.write", body.organization_id)
    return await add(db, m.Brand, **body.model_dump())


@router.post("/merchants/branches", response_model=s.BranchOut, status_code=201, tags=["Merchants"])
async def branch(body: s.BranchIn, actor: Actor, db: DB):
    brand = await Repository(db).require(m.Brand, body.brand_id)
    await scoped(db, actor, "merchant.write", brand.organization_id, body.city_id)
    return await add(db, m.Branch, organization_id=brand.organization_id, **body.model_dump())


@router.get("/merchants/branches", response_model=s.Page[s.BranchOut], tags=["Merchants"])
async def branches(
    db: DB, city_id: UUID | None = None, cursor: str | None = None, limit: Limit = 50
):
    predicates = [
        m.Branch.status == "approved",
        m.Branch.accepting_orders.is_(True),
        m.Branch.city_id.in_(select(m.City.id).where(m.City.active.is_(True))),
    ]
    if city_id:
        predicates.append(m.Branch.city_id == city_id)
    rows, next_id = await Repository(db).page(
        m.Branch, predicates, after=decode_cursor(cursor), limit=limit
    )
    brand_types = (
        {
            row.id: row.merchant_type
            for row in (
                await db.scalars(
                    select(m.Brand).where(m.Brand.id.in_({branch.brand_id for branch in rows}))
                )
            ).all()
        }
        if rows
        else {}
    )
    return {
        "items": [
            s.BranchOut.model_validate(branch).model_copy(
                update={"merchant_type": brand_types.get(branch.brand_id)}
            )
            for branch in rows
        ],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.get("/merchant/branches", response_model=s.Page[s.BranchOut], tags=["Merchant workspace"])
async def merchant_branches(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    """List only branches in active merchant memberships with current branch authority."""
    user_id = UUID(actor.subject)
    assignments = m.RoleAssignment
    branch_row = aliased(m.Branch)
    rows, next_id = await Repository(db).page(
        m.Branch,
        [
            m.Branch.id.in_(
                select(branch_row.id)
                .join(m.Membership, m.Membership.organization_id == branch_row.organization_id)
                .join(m.User, m.User.id == m.Membership.user_id)
                .join(
                    assignments,
                    and_(
                        assignments.user_id == m.Membership.user_id,
                        assignments.organization_id == branch_row.organization_id,
                        or_(
                            assignments.branch_id.is_(None), assignments.branch_id == branch_row.id
                        ),
                        or_(
                            assignments.city_id.is_(None), assignments.city_id == branch_row.city_id
                        ),
                    ),
                )
                .join(m.Role, m.Role.id == assignments.role_id)
                .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
                .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
                .where(
                    branch_row.id == m.Branch.id,
                    m.User.status == "active",
                    m.Membership.user_id == user_id,
                    m.Membership.status == "active",
                    m.Permission.code == "merchant.write",
                )
            )
        ],
        after=decode_cursor(cursor),
        limit=limit,
    )
    if rows:
        brand_rows = await db.scalars(
            select(m.Brand).where(m.Brand.id.in_({branch.brand_id for branch in rows}))
        )
        brand_types = {brand.id: brand.merchant_type for brand in brand_rows.all()}
    else:
        brand_types = {}
    return {
        "items": [
            s.BranchOut.model_validate(branch).model_copy(
                update={"merchant_type": brand_types.get(branch.brand_id)}
            )
            for branch in rows
        ],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.post(
    "/merchants/branches/{branch_id}/review", response_model=s.BranchOut, tags=["Merchants"]
)
async def review_branch(
    branch_id: UUID, body: s.BranchReviewIn, actor: Actor, request: Request, db: DB
):
    branch = await branch_scope(db, actor, branch_id, "merchant.approve", True)
    if branch.version != body.expected_version or branch.status != "pending":
        raise BusinessError("version_conflict", "Branch already reviewed or version changed")
    if branch.organization_id and (
        await db.get(m.Organization, branch.organization_id)
    ).owner_id == UUID(actor.subject):
        raise BusinessError(
            "separation_of_duties", "Onboarding reviewer cannot approve their own organization", 403
        )
    await add(
        db,
        F["merchant.merchant_onboarding_reviews"],
        branch_id=branch.id,
        reviewer_id=UUID(actor.subject),
        decision=body.decision,
        safe_reason=body.reason,
    )
    previous = branch.status
    branch.status, branch.version = body.decision, branch.version + 1
    await audit(
        db,
        actor,
        "merchant.review",
        branch.id,
        request.state.request_id,
        branch.organization_id,
        previous=previous,
        current=branch.status,
    )
    return branch


@router.post(
    "/merchants/branches/{branch_id}/hours",
    response_model=s.IdOut,
    status_code=201,
    tags=["Merchants"],
)
async def hours(branch_id: UUID, body: s.HoursIn, actor: Actor, db: DB):
    await branch_scope(db, actor, branch_id)
    if body.opens_at >= body.closes_at:
        raise BusinessError("invalid_hours", "Split overnight hours into local-day intervals", 422)
    return await add(db, m.OperatingHour, branch_id=branch_id, **body.model_dump())


@router.put(
    "/merchant/branches/{branch_id}/availability",
    response_model=s.BranchOut,
    tags=["Merchant workspace"],
)
async def merchant_availability(
    branch_id: UUID,
    body: s.BranchAvailabilityIn,
    actor: Actor,
    request: Request,
    db: DB,
):
    branch = await branch_scope(db, actor, branch_id, "merchant.write", True)
    if branch.version != body.expected_version:
        raise BusinessError("version_conflict", "Expected version does not match")
    if body.accepting_orders and branch.status != "approved":
        raise BusinessError("branch_not_approved", "Only an approved branch may accept orders", 409)
    previous = branch.accepting_orders
    branch.accepting_orders = body.accepting_orders
    branch.version += 1
    await audit(
        db,
        actor,
        "merchant.availability",
        branch.id,
        request.state.request_id,
        branch.organization_id,
        previous=previous,
        current=branch.accepting_orders,
        version=branch.version,
    )
    return branch


@router.get(
    "/merchant/branches/{branch_id}/catalog",
    response_model=s.Page[s.MerchantCatalogOut],
    tags=["Merchant workspace"],
)
async def merchant_catalog(
    branch_id: UUID,
    actor: Actor,
    db: DB,
    cursor: str | None = None,
    limit: Limit = 50,
):
    await branch_scope(db, actor, branch_id, "catalog.write")
    instant = now()
    statement = (
        select(m.Product, m.Variant, m.Price, m.Stock)
        .join(m.Variant, m.Variant.product_id == m.Product.id)
        .outerjoin(
            m.Price,
            and_(
                m.Price.variant_id == m.Variant.id,
                m.Price.branch_id == branch_id,
                m.Price.starts_at <= instant,
                or_(m.Price.ends_at.is_(None), m.Price.ends_at > instant),
            ),
        )
        .outerjoin(
            m.Stock,
            and_(m.Stock.variant_id == m.Variant.id, m.Stock.branch_id == branch_id),
        )
        .where(m.Product.organization_id == (await db.get(m.Branch, branch_id)).organization_id)
    )
    if cursor:
        statement = statement.where(m.Variant.id > decode_cursor(cursor))
    records = (await db.execute(statement.order_by(m.Variant.id).limit(limit + 1))).all()
    has_more = len(records) > limit
    items = [
        s.MerchantCatalogOut(
            product_id=product.id,
            variant_id=variant.id,
            name=product.name,
            variant_name=variant.name,
            sku=variant.sku,
            unit=product.unit,
            active=product.active,
            currency=price.currency if price else None,
            unit_price=price.amount if price else None,
            on_hand=stock.on_hand if stock else Decimal("0"),
            reserved=stock.reserved if stock else Decimal("0"),
        )
        for product, variant, price, stock in records[:limit]
    ]
    next_cursor = (
        base64.urlsafe_b64encode(items[-1].variant_id.bytes).decode().rstrip("=")
        if has_more and items
        else None
    )
    return {"items": items, "next_cursor": next_cursor}


@router.post(
    "/merchants/branches/{branch_id}/capabilities",
    response_model=s.IdOut,
    status_code=201,
    tags=["Merchants"],
)
async def capability(branch_id: UUID, body: s.CapabilityIn, actor: Actor, db: DB):
    await branch_scope(db, actor, branch_id)
    model = F["merchant.merchant_fulfillment_capabilities"]
    return await add(db, model, branch_id=branch_id, **body.model_dump())


@router.post("/catalog/categories", response_model=s.NamedOut, status_code=201, tags=["Catalogue"])
async def category(body: s.CategoryIn, actor: Actor, db: DB):
    await scoped(db, actor, "geo.write")
    return await add(db, m.Category, **body.model_dump())


@router.get("/catalog/categories", response_model=s.Page[s.NamedOut], tags=["Catalogue"])
async def categories(db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(db, m.Category, [m.Category.regulated.is_(False)], s.NamedOut, cursor, limit)


@router.get("/catalog/products", response_model=s.Page[s.CatalogProductOut], tags=["Catalogue"])
async def customer_catalog(
    actor: Actor,
    db: DB,
    city_id: UUID | None = None,
    branch_id: UUID | None = None,
    category_id: UUID | None = None,
    merchant_type: str | None = None,
    branch_name: CatalogBranchName = None,
    max_price: CatalogMaxPrice = None,
    dietary: CatalogDietary = None,
    q: str | None = Query(default=None, max_length=100),
    cursor: str | None = None,
    limit: Limit = 30,
):
    """Browse currently priced, in-stock products at approved customer-facing branches."""
    instant = now()
    reviews = F["engagement.reviews"]
    average_rating = (
        select(func.avg(reviews.rating))
        .select_from(reviews)
        .join(m.OrderItem, reviews.order_item_id == m.OrderItem.id)
        .join(m.Variant, m.OrderItem.variant_id == m.Variant.id)
        .where(
            m.Variant.product_id == m.Product.id,
            reviews.moderation_status == "published",
        )
        .correlate(m.Product)
        .scalar_subquery()
    )
    review_count = (
        select(func.count(reviews.id))
        .select_from(reviews)
        .join(m.OrderItem, reviews.order_item_id == m.OrderItem.id)
        .join(m.Variant, m.OrderItem.variant_id == m.Variant.id)
        .where(
            m.Variant.product_id == m.Product.id,
            reviews.moderation_status == "published",
        )
        .correlate(m.Product)
        .scalar_subquery()
    )
    statement = (
        select(
            m.Price,
            m.Variant,
            m.Product,
            m.Branch,
            m.Brand,
            m.Category,
            m.Stock,
            average_rating,
            review_count,
        )
        .join(m.Variant, m.Variant.id == m.Price.variant_id)
        .join(m.Product, m.Product.id == m.Variant.product_id)
        .join(m.Branch, m.Branch.id == m.Price.branch_id)
        .join(m.City, m.City.id == m.Branch.city_id)
        .join(m.Brand, m.Brand.id == m.Branch.brand_id)
        .join(m.Category, m.Category.id == m.Product.category_id)
        .join(m.Stock, (m.Stock.branch_id == m.Branch.id) & (m.Stock.variant_id == m.Variant.id))
        .where(
            m.Branch.status == "approved",
            m.Branch.accepting_orders.is_(True),
            m.City.active.is_(True),
            m.Category.regulated.is_(False),
            m.Product.active.is_(True),
            m.Price.starts_at <= instant,
            or_(m.Price.ends_at.is_(None), m.Price.ends_at > instant),
            m.Stock.on_hand > m.Stock.reserved,
        )
    )
    if city_id:
        statement = statement.where(m.Branch.city_id == city_id)
    if branch_id:
        statement = statement.where(m.Branch.id == branch_id)
    if category_id:
        statement = statement.where(m.Product.category_id == category_id)
    if merchant_type:
        statement = statement.where(m.Brand.merchant_type == merchant_type)
    if branch_name and branch_name.strip():
        statement = statement.where(m.Branch.name.ilike(f"%{branch_name.strip()}%"))
    if max_price is not None:
        statement = statement.where(m.Price.amount <= max_price)
    if dietary:
        invalid_code = any(
            not code or len(code) > 32 or not code.replace("_", "").isalnum() for code in dietary
        )
        if invalid_code:
            raise BusinessError(
                "invalid_dietary_filter", "Dietary filters must be short codes", 422
            )
        dietary_attributes = F["catalog.dietary_attributes"]
        for code in set(code.lower() for code in dietary):
            statement = statement.where(
                select(dietary_attributes.id)
                .where(
                    dietary_attributes.product_id == m.Product.id,
                    dietary_attributes.dietary_code == code,
                )
                .exists()
            )
    if q and q.strip():
        pattern = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                m.Product.name.ilike(pattern),
                m.Variant.name.ilike(pattern),
                m.Branch.name.ilike(pattern),
                m.Brand.name.ilike(pattern),
            )
        )
    if cursor:
        statement = statement.where(m.Price.id > decode_cursor(cursor))
    rows = (await db.execute(statement.order_by(m.Price.id).limit(limit + 1))).all()
    has_more = len(rows) > limit
    items = []
    for (
        price,
        variant,
        product,
        branch,
        brand,
        category_row,
        stock,
        rating_average,
        rating_count,
    ) in rows[:limit]:
        items.append(
            s.CatalogProductOut(
                id=price.id,
                product_id=product.id,
                variant_id=variant.id,
                branch_id=branch.id,
                branch_name=branch.name,
                merchant_type=brand.merchant_type,
                category_id=category_row.id,
                category_name=category_row.name,
                name=product.name,
                variant_name=variant.name,
                unit=product.unit,
                variable_weight=product.variable_weight,
                currency=price.currency,
                unit_price=price.amount,
                available_quantity=stock.on_hand - stock.reserved,
                average_rating=rating_average,
                review_count=rating_count,
            )
        )
    next_cursor = None
    if has_more and items:
        next_cursor = base64.urlsafe_b64encode(items[-1].id.bytes).decode().rstrip("=")
    return {"items": items, "next_cursor": next_cursor}


@router.post("/catalog/products", response_model=s.ProductOut, status_code=201, tags=["Catalogue"])
async def product(body: s.ProductIn, actor: Actor, db: DB):
    await scoped(db, actor, "catalog.write", body.organization_id)
    return await add(db, m.Product, **body.model_dump())


@router.post(
    "/catalog/products/{product_id}/variants",
    response_model=s.VariantOut,
    status_code=201,
    tags=["Catalogue"],
)
async def variant(product_id: UUID, body: s.VariantIn, actor: Actor, db: DB):
    product = await Repository(db).require(m.Product, product_id)
    await scoped(db, actor, "catalog.write", product.organization_id)
    return await add(db, m.Variant, product_id=product.id, **body.model_dump())


@router.post(
    "/merchants/branches/{branch_id}/prices",
    response_model=s.PriceOut,
    status_code=201,
    tags=["Catalogue"],
)
async def price(branch_id: UUID, body: s.PriceIn, actor: Actor, db: DB):
    branch = await branch_scope(db, actor, branch_id, "catalog.write", True)
    variant = await Repository(db).require(m.Variant, body.variant_id)
    product = await Repository(db).require(m.Product, variant.product_id)
    if product.organization_id != branch.organization_id:
        raise BusinessError("forbidden", "Product belongs to another organization", 403)
    currency = await db.scalar(select(m.Currency).where(m.Currency.code == body.currency))
    if not currency or body.amount != money(body.amount, currency.scale):
        raise BusinessError(
            "currency_precision", "Configure currency and use its permitted precision", 422
        )
    if body.ends_at and body.ends_at <= body.starts_at:
        raise BusinessError("invalid_period", "Price end must follow start", 422)
    # Branch lock serializes overlapping price updates without a mandatory extension.
    overlaps = select(m.Price.id).where(
        m.Price.branch_id == branch_id,
        m.Price.variant_id == body.variant_id,
        (m.Price.ends_at.is_(None)) | (m.Price.ends_at > body.starts_at),
    )
    if body.ends_at:
        overlaps = overlaps.where(m.Price.starts_at < body.ends_at)
    if await db.scalar(overlaps):
        raise BusinessError("overlapping_price", "Price period overlaps an existing branch price")
    # Register an empty balance so a newly priced variant is reachable from the
    # inventory screen. This does not grant stock or make the product sellable.
    await db.execute(
        insert(m.Stock)
        .values(branch_id=branch_id, variant_id=body.variant_id, on_hand=0, reserved=0, version=1)
        .on_conflict_do_nothing(index_elements=["branch_id", "variant_id"])
    )
    return await add(db, m.Price, branch_id=branch_id, **body.model_dump())


@router.get(
    "/merchants/branches/{branch_id}/prices", response_model=s.Page[s.PriceOut], tags=["Catalogue"]
)
async def prices(branch_id: UUID, db: DB, cursor: str | None = None, limit: Limit = 50):
    branch = await Repository(db).require(m.Branch, branch_id)
    city = await db.get(m.City, branch.city_id)
    if branch.status != "approved" or not branch.accepting_orders or not city or not city.active:
        raise BusinessError("not_found", "Resource not found", 404)
    instant = now()
    return await page(
        db,
        m.Price,
        [
            m.Price.branch_id == branch_id,
            m.Price.starts_at <= instant,
            or_(m.Price.ends_at.is_(None), m.Price.ends_at > instant),
        ],
        s.PriceOut,
        cursor,
        limit,
    )


@router.post(
    "/merchants/branches/{branch_id}/windows",
    response_model=s.WindowOut,
    status_code=201,
    tags=["Fulfillment"],
)
async def window(branch_id: UUID, body: s.WindowIn, actor: Actor, db: DB):
    await branch_scope(db, actor, branch_id)
    if body.ends_at <= body.starts_at or body.starts_at <= now():
        raise BusinessError("invalid_window", "Window must be future and end after its start", 422)
    return await add(db, m.Window, branch_id=branch_id, **body.model_dump())


@router.get(
    "/merchants/branches/{branch_id}/windows",
    response_model=s.Page[s.WindowOut],
    tags=["Fulfillment"],
)
async def windows(branch_id: UUID, db: DB, cursor: str | None = None, limit: Limit = 50):
    branch = await db.get(m.Branch, branch_id)
    if not branch or branch.status != "approved" or not branch.accepting_orders:
        raise BusinessError("not_found", "Resource not found", 404)
    city = await db.get(m.City, branch.city_id)
    if not city or not city.active:
        raise BusinessError("not_found", "Resource not found", 404)
    return await page(
        db,
        m.Window,
        [m.Window.branch_id == branch_id, m.Window.ends_at > now()],
        s.WindowOut,
        cursor,
        limit,
    )


@router.post(
    "/inventory/branches/{branch_id}/adjustments", response_model=s.StockOut, tags=["Inventory"]
)
async def adjust_stock(branch_id: UUID, body: s.StockAdjustmentIn, actor: Actor, db: DB):
    await branch_scope(db, actor, branch_id, "inventory.write", True)
    variant = await Repository(db).require(m.Variant, body.variant_id)
    product = await Repository(db).require(m.Product, variant.product_id)
    branch = await db.get(m.Branch, branch_id)
    if product.organization_id != branch.organization_id:
        raise BusinessError("forbidden", "Inventory product belongs to another organization", 403)
    key = f"adjust:{branch_id}:{body.idempotency_key}"
    prior = await db.scalar(select(m.StockMovement).where(m.StockMovement.idempotency_key == key))
    if prior:
        stock = await db.get(m.Stock, prior.stock_id)
        if (
            stock.variant_id != body.variant_id
            or prior.quantity != body.delta
            or prior.batch_id != body.batch_id
        ):
            raise BusinessError(
                "idempotency_conflict", "Adjustment key was used for different stock"
            )
        return stock
    await db.execute(
        insert(m.Stock)
        .values(branch_id=branch_id, variant_id=body.variant_id, on_hand=0, reserved=0, version=1)
        .on_conflict_do_nothing(index_elements=["branch_id", "variant_id"])
    )
    stock = await db.scalar(
        select(m.Stock)
        .where(m.Stock.branch_id == branch_id, m.Stock.variant_id == body.variant_id)
        .with_for_update()
    )
    if stock.on_hand + body.delta < stock.reserved:
        raise BusinessError("negative_stock", "Adjustment would make sellable stock negative")
    batch_model = F["inventory.stock_batches"]
    batched = await db.scalar(
        select(batch_model.id).where(batch_model.stock_id == stock.id).limit(1)
    )
    if batched:
        if not body.batch_id:
            raise BusinessError(
                "batch_required", "Batch-tracked adjustments require a batch identifier"
            )
        batch = await Repository(db).require(batch_model, body.batch_id, lock=True)
        if batch.stock_id != stock.id or batch.quantity + body.delta < batch.reserved:
            raise BusinessError(
                "invalid_batch_adjustment",
                "Batch does not match or adjustment would consume reservations",
            )
        batch.quantity += body.delta
    elif body.batch_id:
        raise BusinessError("invalid_batch", "Batch is not part of this stock", 422)
    stock.on_hand += body.delta
    stock.version += 1
    await add(
        db,
        m.StockMovement,
        stock_id=stock.id,
        batch_id=body.batch_id,
        quantity=body.delta,
        kind="adjust",
        idempotency_key=key,
        actor_id=UUID(actor.subject),
    )
    return stock


@router.post(
    "/inventory/branches/{branch_id}/batches",
    response_model=s.IdOut,
    status_code=201,
    tags=["Inventory"],
)
async def receive_batch(branch_id: UUID, body: s.BatchIn, actor: Actor, db: DB):
    branch = await branch_scope(db, actor, branch_id, "inventory.write", True)
    variant = await Repository(db).require(m.Variant, body.variant_id)
    product = await Repository(db).require(m.Product, variant.product_id)
    if product.organization_id != branch.organization_id:
        raise BusinessError("forbidden", "Product is outside this organization", 403)
    key = f"receive:{branch_id}:{body.idempotency_key}"
    prior = await db.scalar(select(m.StockMovement).where(m.StockMovement.idempotency_key == key))
    if prior:
        previous_batch = await db.get(F["inventory.stock_batches"], prior.batch_id)
        previous_expiry = await db.scalar(
            select(F["inventory.expiry_dates"].expires_on).where(
                F["inventory.expiry_dates"].batch_id == prior.batch_id
            )
        )
        if (
            prior.quantity != body.quantity
            or previous_batch.lot_code != body.lot_code
            or previous_expiry != body.expires_on
        ):
            raise BusinessError("idempotency_conflict", "Batch receipt key payload changed")
        return previous_batch
    if body.expires_on and body.expires_on < now().date():
        raise BusinessError("expired_batch", "Cannot receive already expired sellable stock", 422)
    await db.execute(
        insert(m.Stock)
        .values(branch_id=branch_id, variant_id=body.variant_id, on_hand=0, reserved=0, version=1)
        .on_conflict_do_nothing(index_elements=["branch_id", "variant_id"])
    )
    stock = await db.scalar(
        select(m.Stock)
        .where(m.Stock.branch_id == branch_id, m.Stock.variant_id == body.variant_id)
        .with_for_update()
    )
    batch_model = F["inventory.stock_batches"]
    has_batches = await db.scalar(
        select(batch_model.id).where(batch_model.stock_id == stock.id).limit(1)
    )
    if not has_batches and stock.on_hand != 0:
        raise BusinessError(
            "batch_reconciliation_required",
            "Reconcile existing unbatched stock before enabling batch tracking",
        )
    batch = await add(
        db,
        batch_model,
        stock_id=stock.id,
        lot_code=body.lot_code,
        quantity=body.quantity,
        reserved=0,
        received_at=now(),
    )
    if body.expires_on:
        await add(db, F["inventory.expiry_dates"], batch_id=batch.id, expires_on=body.expires_on)
    stock.on_hand += body.quantity
    stock.version += 1
    await add(
        db,
        m.StockMovement,
        stock_id=stock.id,
        batch_id=batch.id,
        quantity=body.quantity,
        kind="batch_receive",
        idempotency_key=key,
        actor_id=UUID(actor.subject),
    )
    return batch


@router.get(
    "/inventory/branches/{branch_id}/batches",
    response_model=list[s.StockBatchOut],
    tags=["Inventory"],
)
async def stock_batches(branch_id: UUID, actor: Actor, db: DB, limit: Limit = 100):
    await branch_scope(db, actor, branch_id, "inventory.read")
    Batch, Expiry = F["inventory.stock_batches"], F["inventory.expiry_dates"]
    rows = (
        await db.execute(
            select(Batch, m.Stock, Expiry.expires_on)
            .join(m.Stock, Batch.stock_id == m.Stock.id)
            .outerjoin(Expiry, Expiry.batch_id == Batch.id)
            .where(m.Stock.branch_id == branch_id)
            .order_by(Expiry.expires_on.asc().nulls_last(), Batch.received_at, Batch.id)
            .limit(limit)
        )
    ).all()
    return [
        s.StockBatchOut(
            id=batch.id,
            branch_id=stock.branch_id,
            variant_id=stock.variant_id,
            lot_code=batch.lot_code,
            quantity=batch.quantity,
            reserved=batch.reserved,
            expires_on=expires_on,
            received_at=batch.received_at,
        )
        for batch, stock, expires_on in rows
    ]


@router.get(
    "/inventory/branches/{branch_id}", response_model=s.Page[s.StockOut], tags=["Inventory"]
)
async def stock_status(
    branch_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    await branch_scope(db, actor, branch_id, "inventory.read")
    return await page(db, m.Stock, [m.Stock.branch_id == branch_id], s.StockOut, cursor, limit)


@router.post("/carts", response_model=s.VersionOut, status_code=201, tags=["Commerce"])
async def cart(actor: Actor, db: DB):
    return await add(db, m.Cart, user_id=UUID(actor.subject))


@router.get("/carts/{cart_id}", response_model=s.VersionOut, tags=["Commerce"])
async def get_cart(cart_id: UUID, actor: Actor, db: DB):
    cart = await commerce.cart_context(db, actor, cart_id)
    return cart


@router.post(
    "/carts/{cart_id}/items", response_model=s.CartItemOut, status_code=201, tags=["Commerce"]
)
async def cart_item(cart_id: UUID, body: s.CartItemIn, actor: Actor, db: DB):
    return await commerce.add_item(db, actor, cart_id, body)


@router.get("/carts/{cart_id}/items", response_model=s.Page[s.CartItemOut], tags=["Commerce"])
async def cart_items(
    cart_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    cart = await Repository(db).require(m.Cart, cart_id)
    owned(actor, cart.user_id)
    predicates = [m.CartItem.cart_id == cart.id]
    rows, next_id = await Repository(db).page(
        m.CartItem, predicates, after=decode_cursor(cursor), limit=limit
    )
    if not rows:
        return {"items": [], "next_cursor": None}
    details = (
        await db.execute(
            select(
                m.CartItem.id,
                m.Product.name,
                m.Variant.name,
                m.Branch.name,
                m.Window.starts_at,
                m.Window.ends_at,
            )
            .join(m.Variant, m.Variant.id == m.CartItem.variant_id)
            .join(m.Product, m.Product.id == m.Variant.product_id)
            .join(m.Branch, m.Branch.id == m.CartItem.branch_id)
            .join(m.Window, m.Window.id == m.CartItem.window_id)
            .where(m.CartItem.id.in_([row.id for row in rows]))
        )
    ).all()
    by_id = {row[0]: row[1:] for row in details}
    items = []
    for row in rows:
        names = by_id.get(row.id, (None, None, None))
        items.append(
            s.CartItemOut.model_validate(row).model_copy(
                update={
                    "product_name": names[0],
                    "variant_name": names[1],
                    "branch_name": names[2],
                    "window_starts_at": names[3],
                    "window_ends_at": names[4],
                }
            )
        )
    return {
        "items": items,
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.delete("/carts/{cart_id}/items/{item_id}", status_code=204, tags=["Commerce"])
async def remove_item(cart_id: UUID, item_id: UUID, actor: Actor, db: DB):
    cart = await commerce.cart_context(db, actor, cart_id)
    item = await Repository(db).require(m.CartItem, item_id)
    if item.cart_id != cart.id:
        raise BusinessError("not_found", "Cart item not found", 404)
    await db.delete(item)
    cart.version += 1
    return Response(status_code=204)


@router.post(
    "/carts/{cart_id}/quote", response_model=s.QuoteOut, status_code=201, tags=["Commerce"]
)
async def quote(cart_id: UUID, actor: Actor, db: DB):
    quote_row = await commerce.make_quote(db, actor, cart_id)
    payload = s.QuoteOut.model_validate(quote_row).model_dump()
    import copy

    lines = copy.deepcopy(quote_row.snapshot.get("lines", []))
    branch_ids = {UUID(line["branch_id"]) for line in lines}
    window_ids = {UUID(line["window_id"]) for line in lines}
    branches_by_id = (
        {
            row.id: row.name
            for row in (await db.scalars(select(m.Branch).where(m.Branch.id.in_(branch_ids)))).all()
        }
        if branch_ids
        else {}
    )
    windows_by_id = (
        {
            row.id: row
            for row in (await db.scalars(select(m.Window).where(m.Window.id.in_(window_ids)))).all()
        }
        if window_ids
        else {}
    )
    for line in lines:
        branch_id, window_id = UUID(line["branch_id"]), UUID(line["window_id"])
        line["branch_name"] = branches_by_id.get(branch_id)
        window = windows_by_id.get(window_id)
        line["window_starts_at"] = window.starts_at if window else None
        line["window_ends_at"] = window.ends_at if window else None
        address = line.get("address") or {}
        line["delivery_address"] = address.get("address_text")
    payload["lines"] = lines
    from decimal import Decimal

    item_subtotal = sum(
        (Decimal(line["unit_price"]) * Decimal(line["quantity"]) for line in lines), Decimal(0)
    )
    payload["breakdown"] = {
        "items": item_subtotal,
        "extras": sum((Decimal(line["total"]) for line in lines), Decimal(0)) - item_subtotal,
        "delivery": sum(
            (Decimal(group["delivery_fee"]) for group in quote_row.snapshot.get("shipments", [])),
            Decimal(0),
        ),
        "taxes": Decimal(0),
        "discounts": Decimal(0),
        "total": quote_row.total,
    }
    payload["shipments"] = quote_row.snapshot.get("shipments", [])
    return payload


@router.post("/orders/confirm", response_model=s.OrderOut, status_code=201, tags=["Commerce"])
async def confirm(body: s.ConfirmIn, actor: Actor, request: Request, db: DB, idempotency_key: Key):
    return await commerce.confirm(
        db, actor, body.quote_id, idempotency_key, request.state.request_id
    )


@router.get("/orders", response_model=s.Page[s.OrderOut], tags=["Commerce"])
async def orders(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(
        db, m.Order, [m.Order.user_id == UUID(actor.subject)], s.OrderOut, cursor, limit
    )


@router.get("/orders/{order_id}", response_model=s.OrderOut, tags=["Commerce"])
async def order(order_id: UUID, actor: Actor, db: DB):
    row = await Repository(db).require(m.Order, order_id)
    owned(actor, row.user_id)
    return row


@router.get(
    "/orders/{order_id}/reviewable-items",
    response_model=s.Page[s.ReviewableOrderItemOut],
    tags=["Customer feedback"],
)
async def reviewable_order_items(
    order_id: UUID,
    actor: Actor,
    db: DB,
    cursor: str | None = None,
    limit: Limit = 50,
):
    order_row = await Repository(db).require(m.Order, order_id)
    owned(actor, order_row.user_id)
    reviews = F["engagement.reviews"]
    statement = (
        select(m.OrderItem, reviews.rating)
        .join(
            m.FulfillmentUnit,
            m.FulfillmentUnit.id == m.OrderItem.fulfillment_unit_id,
        )
        .join(m.MerchantOrder, m.MerchantOrder.id == m.OrderItem.merchant_order_id)
        .outerjoin(
            reviews,
            and_(
                reviews.order_item_id == m.OrderItem.id,
                reviews.user_id == UUID(actor.subject),
            ),
        )
        .where(
            m.MerchantOrder.order_id == order_row.id,
            m.FulfillmentUnit.status == "delivered",
        )
    )
    if cursor:
        statement = statement.where(m.OrderItem.id > decode_cursor(cursor))
    rows = (await db.execute(statement.order_by(m.OrderItem.id).limit(limit + 1))).all()
    has_more = len(rows) > limit
    items = [
        {
            "id": item.id,
            "product_name": item.product_name,
            "variant_name": item.variant_name,
            "rating": rating,
        }
        for item, rating in rows[:limit]
    ]
    next_cursor = (
        base64.urlsafe_b64encode(items[-1]["id"].bytes).decode().rstrip("=")
        if has_more and items
        else None
    )
    return {"items": items, "next_cursor": next_cursor}


@router.post(
    "/order-items/{order_item_id}/review",
    response_model=s.CustomerReviewOut,
    status_code=201,
    tags=["Customer feedback"],
)
async def submit_order_item_review(
    order_item_id: UUID,
    body: s.CustomerProductRatingIn,
    actor: Actor,
    request: Request,
    db: DB,
):
    await actor_budget(request, actor, "customer-product-review", 20)
    row = await db.execute(
        select(m.OrderItem, m.FulfillmentUnit, m.MerchantOrder, m.Order)
        .join(m.FulfillmentUnit, m.FulfillmentUnit.id == m.OrderItem.fulfillment_unit_id)
        .join(m.MerchantOrder, m.MerchantOrder.id == m.OrderItem.merchant_order_id)
        .join(m.Order, m.Order.id == m.MerchantOrder.order_id)
        .where(m.OrderItem.id == order_item_id)
        .with_for_update(of=m.OrderItem)
    )
    item, unit, child, order_row = row.first() or (None, None, None, None)
    if item is None:
        raise BusinessError("not_found", "Order item not found", 404)
    owned(actor, order_row.user_id)
    if unit.status != "delivered":
        raise BusinessError("review_requires_delivery", "Only delivered items can be rated", 409)
    reviews = F["engagement.reviews"]
    existing = await db.scalar(
        select(reviews).where(
            reviews.user_id == UUID(actor.subject),
            reviews.order_item_id == item.id,
        )
    )
    if existing:
        if existing.rating == body.rating:
            return existing
        raise BusinessError("review_already_submitted", "This item has already been rated", 409)
    branch = await Repository(db).require(m.Branch, child.branch_id)
    review = await add(
        db,
        reviews,
        user_id=UUID(actor.subject),
        order_item_id=item.id,
        rating=body.rating,
        body="",
        moderation_status="published",
    )
    await audit(
        db,
        actor,
        "customer.product_rating.create",
        review.id,
        request.state.request_id,
        branch.organization_id,
        current=body.rating,
    )
    return review


@router.get("/orders/{order_id}/payment", response_model=s.PaymentOut, tags=["Finance"])
async def order_payment(order_id: UUID, actor: Actor, db: DB):
    row = await Repository(db).require(m.Order, order_id)
    owned(actor, row.user_id)
    payment = await db.scalar(
        select(m.PaymentIntent)
        .where(
            m.PaymentIntent.order_id == row.id,
            m.PaymentIntent.provider.in_(("sandbox", "razorpay")),
        )
        .order_by(m.PaymentIntent.created_at.desc())
    )
    if payment is None:
        raise BusinessError(
            "payment_not_found", "No online payment intent exists for this order", 404
        )
    return payment


@router.get(
    "/orders/{order_id}/merchant-orders", response_model=s.Page[s.ChildOut], tags=["Commerce"]
)
async def children(
    order_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    row = await Repository(db).require(m.Order, order_id)
    owned(actor, row.user_id)
    return await page(
        db, m.MerchantOrder, [m.MerchantOrder.order_id == row.id], s.ChildOut, cursor, limit
    )


@router.get(
    "/orders/{order_id}/reorder-lines",
    response_model=list[s.ReorderLineOut],
    tags=["Commerce"],
)
async def reorder_lines(order_id: UUID, actor: Actor, db: DB):
    order = await Repository(db).require(m.Order, order_id)
    owned(actor, order.user_id)
    rows = (
        await db.execute(
            select(m.OrderItem, m.FulfillmentUnit, m.MerchantOrder, m.Branch)
            .join(m.FulfillmentUnit, m.OrderItem.fulfillment_unit_id == m.FulfillmentUnit.id)
            .join(m.MerchantOrder, m.OrderItem.merchant_order_id == m.MerchantOrder.id)
            .join(m.Branch, m.MerchantOrder.branch_id == m.Branch.id)
            .where(m.MerchantOrder.order_id == order.id)
            .order_by(m.OrderItem.id)
            .limit(100)
        )
    ).all()
    return [
        s.ReorderLineOut(
            branch_id=branch.id,
            branch_name=branch.name,
            variant_id=item.variant_id,
            product_name=item.product_name,
            variant_name=item.variant_name,
            quantity=item.quantity,
            delivery_method=unit.delivery_method,
            address_id=UUID((item.snapshot.get("address") or {})["id"])
            if (item.snapshot.get("address") or {}).get("id")
            else None,
        )
        for item, unit, _child, branch in rows
    ]


def merchant_queue_item(item):
    snapshot = item.snapshot or {}
    return s.MerchantQueueItem.model_validate(item, from_attributes=True).model_copy(
        update={
            "preparation_notes": snapshot.get("preparation_notes", ""),
            "addons": snapshot.get("addons", []),
        }
    )


@router.get(
    "/merchant/branches/{branch_id}/orders",
    response_model=s.MerchantQueuePage,
    tags=["Merchant workspace"],
)
async def merchant_order_queue(
    branch_id: UUID,
    actor: Actor,
    db: DB,
    cursor: str | None = None,
    limit: Limit = 50,
):
    await branch_scope(db, actor, branch_id, "merchant.write")
    children, next_id = await Repository(db).page(
        m.MerchantOrder,
        [m.MerchantOrder.branch_id == branch_id],
        after=decode_cursor(cursor),
        limit=limit,
    )
    item_rows = (
        (
            await db.scalars(
                select(m.OrderItem)
                .where(m.OrderItem.merchant_order_id.in_({child.id for child in children}))
                .order_by(m.OrderItem.created_at, m.OrderItem.id)
            )
        ).all()
        if children
        else []
    )
    items_by_order: dict[UUID, list[s.MerchantQueueItem]] = {}
    for item in item_rows:
        items_by_order.setdefault(item.merchant_order_id, []).append(merchant_queue_item(item))
    return {
        "items": [
            s.MerchantQueueOut.model_validate(child).model_copy(
                update={"items": items_by_order.get(child.id, [])}
            )
            for child in children
        ],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.get("/merchant/branches/{branch_id}/orders/{child_id}", tags=["Merchant workspace"])
async def merchant_order_detail(branch_id: UUID, child_id: UUID, actor: Actor, db: DB):
    await branch_scope(db, actor, branch_id, "merchant.write")
    child = await db.scalar(
        select(m.MerchantOrder).where(
            m.MerchantOrder.id == child_id, m.MerchantOrder.branch_id == branch_id
        )
    )
    if child is None:
        raise BusinessError("not_found", "Order not found in this branch", 404)
    item_rows = (
        await db.scalars(
            select(m.OrderItem)
            .where(m.OrderItem.merchant_order_id == child.id)
            .order_by(m.OrderItem.created_at, m.OrderItem.id)
        )
    ).all()
    order = await Repository(db).require(m.Order, child.order_id)
    Profile = F["identity.user_profiles"]
    profile = await db.scalar(select(Profile).where(Profile.user_id == order.user_id))
    units = (
        await db.scalars(
            select(m.FulfillmentUnit).where(m.FulfillmentUnit.merchant_order_id == child.id)
        )
    ).all()
    # Fulfillment context only, restricted to the merchant's own order.
    return {
        **s.MerchantQueueOut.model_validate(child).model_dump(),
        "items": [merchant_queue_item(item) for item in item_rows],
        "customer": {"display_name": profile.display_name if profile else "Customer"},
        "fulfillment": [
            {
                "delivery_method": unit.delivery_method,
                "address": unit.address_snapshot
                if unit.delivery_method == "merchant_delivery"
                and child.status not in {"fulfilled", "rejected", "cancelled"}
                else None,
            }
            for unit in units
        ],
    }


@router.post(
    "/merchant/branches/{branch_id}/kitchen/stations",
    response_model=s.KitchenStationOut,
    status_code=201,
    tags=["Merchant workspace"],
)
async def create_kitchen_station(
    branch_id: UUID, body: s.KitchenStationIn, actor: Actor, request: Request, db: DB
):
    branch = await branch_scope(db, actor, branch_id, "kitchen.manage", True)
    if await db.scalar(
        select(m.KitchenStation.id).where(
            m.KitchenStation.branch_id == branch.id,
            func.lower(m.KitchenStation.name) == body.name.lower(),
        )
    ):
        raise BusinessError("station_exists", "A station with this name already exists", 409)
    station = await add(
        db, m.KitchenStation, branch_id=branch.id, **body.model_dump(), active=True, version=1
    )
    await audit(
        db,
        actor,
        "merchant.kitchen_station_created",
        station.id,
        request.state.request_id,
        branch.organization_id,
        version=1,
    )
    await db.refresh(station)
    return station


@router.get(
    "/merchant/branches/{branch_id}/kitchen/stations",
    response_model=list[s.KitchenStationOut],
    tags=["Merchant workspace"],
)
async def kitchen_stations(branch_id: UUID, actor: Actor, db: DB):
    await branch_scope(db, actor, branch_id, "kitchen.manage")
    return (
        await db.scalars(
            select(m.KitchenStation)
            .where(m.KitchenStation.branch_id == branch_id)
            .order_by(m.KitchenStation.is_packaging, m.KitchenStation.name)
        )
    ).all()


@router.get(
    "/merchant/branches/{branch_id}/kitchen/tasks",
    response_model=s.KitchenTaskPage,
    tags=["Merchant workspace"],
)
async def kitchen_tasks(
    branch_id: UUID,
    actor: Actor,
    db: DB,
    station_id: UUID | None = None,
    status: str | None = None,
    cursor: str | None = None,
    limit: Limit = 100,
):
    await branch_scope(db, actor, branch_id, "kitchen.manage")
    predicates = [m.KitchenTask.branch_id == branch_id]
    if station_id:
        predicates.append(m.KitchenTask.station_id == station_id)
    if status:
        if status not in {"pending", "in_progress", "paused", "completed"}:
            raise BusinessError("invalid_task_status", "Unknown kitchen task status", 422)
        predicates.append(m.KitchenTask.status == status)
    rows, next_id = await Repository(db).page(
        m.KitchenTask, predicates, after=decode_cursor(cursor), limit=limit
    )
    station_ids = {row.station_id for row in rows}
    stations = (
        (
            await db.scalars(select(m.KitchenStation).where(m.KitchenStation.id.in_(station_ids)))
        ).all()
        if station_ids
        else []
    )
    station_names = {row.id: row.name for row in stations}
    blockers = {}
    if rows:
        pairs = (
            await db.execute(
                select(m.KitchenTaskDependency.task_id, m.KitchenTaskDependency.depends_on_task_id)
                .join(m.KitchenTask, m.KitchenTask.id == m.KitchenTaskDependency.depends_on_task_id)
                .where(
                    m.KitchenTaskDependency.task_id.in_([r.id for r in rows]),
                    m.KitchenTask.status != "completed",
                )
            )
        ).all()
        for task_id, dependency_id in pairs:
            blockers.setdefault(task_id, []).append(dependency_id)
    return {
        "items": [
            s.KitchenTaskOut.model_validate(
                {
                    **{
                        column.name: getattr(row, column.name)
                        for column in m.KitchenTask.__table__.columns
                    },
                    "station_name": station_names[row.station_id],
                    "blocked_by": blockers.get(row.id, []),
                }
            )
            for row in rows
        ],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.put(
    "/merchant/kitchen/tasks/{task_id}/station",
    response_model=s.KitchenTaskOut,
    tags=["Merchant workspace"],
)
async def reassign_kitchen_task(
    task_id: UUID, body: s.KitchenTaskStationIn, actor: Actor, request: Request, db: DB
):
    task = await Repository(db).require(m.KitchenTask, task_id, lock=True)
    branch = await branch_scope(db, actor, task.branch_id, "kitchen.manage", True)
    if task.version != body.expected_version:
        raise BusinessError("version_conflict", "Expected version does not match")
    if task.status != "pending":
        raise BusinessError("task_already_started", "Only pending tasks can be reassigned", 409)
    station = await Repository(db).require(m.KitchenStation, body.station_id)
    if station.branch_id != branch.id or not station.active:
        raise BusinessError("invalid_station", "Station is unavailable for this branch", 422)
    if station.is_packaging != (task.task_type == "packing"):
        raise BusinessError("station_type_mismatch", "Task requires a matching station type", 422)
    task.station_id = station.id
    task.version += 1
    await audit(
        db,
        actor,
        "merchant.kitchen_task_reassigned",
        task.id,
        request.state.request_id,
        branch.organization_id,
        version=task.version,
    )
    await db.refresh(task)
    return await _kitchen_task_out(db, task)


@router.post(
    "/merchant/kitchen/tasks/{task_id}/transition",
    response_model=s.KitchenTaskOut,
    tags=["Merchant workspace"],
)
async def transition_kitchen_task(
    task_id: UUID, body: s.KitchenTaskTransitionIn, actor: Actor, request: Request, db: DB
):
    task = await Repository(db).require(m.KitchenTask, task_id, lock=True)
    branch = await branch_scope(db, actor, task.branch_id, "kitchen.manage")
    if task.status == body.target:
        return await _kitchen_task_out(db, task)
    if task.version != body.expected_version:
        raise BusinessError("version_conflict", "Expected version does not match")
    child = await Repository(db).require(m.MerchantOrder, task.merchant_order_id, lock=True)
    if child.status != "preparing":
        raise BusinessError("order_not_preparing", "Kitchen work requires a preparing order", 409)
    allowed = {
        "pending": {"in_progress"},
        "in_progress": {"paused", "completed"},
        "paused": {"in_progress"},
        "completed": set(),
    }
    if body.target not in allowed[task.status]:
        raise BusinessError(
            "invalid_task_transition", "Kitchen task transition is not allowed", 409
        )
    station = await Repository(db).require(m.KitchenStation, task.station_id, lock=True)
    if not station.active:
        raise BusinessError("station_unavailable", "Kitchen station is inactive", 409)
    if body.target == "in_progress":
        blockers = await db.scalar(
            select(m.KitchenTaskDependency.id)
            .join(m.KitchenTask, m.KitchenTask.id == m.KitchenTaskDependency.depends_on_task_id)
            .where(m.KitchenTaskDependency.task_id == task.id, m.KitchenTask.status != "completed")
            .limit(1)
        )
        if blockers:
            raise BusinessError("task_blocked", "Complete prerequisite tasks first", 409)
        active_count = await db.scalar(
            select(func.count())
            .select_from(m.KitchenTask)
            .where(
                m.KitchenTask.station_id == station.id,
                m.KitchenTask.status == "in_progress",
                m.KitchenTask.id != task.id,
            )
        )
        if int(active_count or 0) >= station.max_concurrent:
            raise BusinessError(
                "station_at_capacity", "Station has reached concurrent task capacity", 409
            )
        task.started_at = task.started_at or now()
    previous = task.status
    task.status = body.target
    task.version += 1
    if body.target == "completed":
        task.completed_at = now()
    await audit(
        db,
        actor,
        "merchant.kitchen_task_transitioned",
        task.id,
        request.state.request_id,
        branch.organization_id,
        version=task.version,
        previous=previous,
        current=body.target,
    )
    await db.refresh(task)
    return await _kitchen_task_out(db, task)


async def _kitchen_task_out(db, task):
    station = await db.get(m.KitchenStation, task.station_id)
    blockers = (
        await db.scalars(
            select(m.KitchenTaskDependency.depends_on_task_id)
            .join(m.KitchenTask, m.KitchenTask.id == m.KitchenTaskDependency.depends_on_task_id)
            .where(m.KitchenTaskDependency.task_id == task.id, m.KitchenTask.status != "completed")
        )
    ).all()
    return s.KitchenTaskOut.model_validate(
        {
            **{
                column.name: getattr(task, column.name)
                for column in m.KitchenTask.__table__.columns
            },
            "station_name": station.name,
            "blocked_by": list(blockers),
        }
    )


@router.post("/merchant-orders/{child_id}/transition", response_model=s.ChildOut, tags=["Commerce"])
async def child_transition(
    child_id: UUID, body: s.TransitionIn, actor: Actor, request: Request, db: DB
):
    return await commerce.merchant_transition(
        db, actor, child_id, body.target, body.expected_version, request.state.request_id
    )


@router.post("/pilots", response_model=s.IdOut, status_code=201, tags=["Fulfillment"])
async def pilot(body: s.PilotIn, actor: Actor, db: DB):
    return await add(db, m.Pilot, user_id=UUID(actor.subject), city_id=body.city_id)


@router.post("/pilots/{pilot_id}/verify", response_model=s.IdOut, tags=["Fulfillment"])
async def verify_pilot(pilot_id: UUID, actor: Actor, db: DB):
    await scoped(db, actor, "pilot.verify")
    pilot = await Repository(db).require(m.Pilot, pilot_id, lock=True)
    pilot.verified = True
    return pilot


@router.put("/pilots/{pilot_id}/availability", response_model=s.IdOut, tags=["Fulfillment"])
async def availability(pilot_id: UUID, body: s.AvailableIn, actor: Actor, db: DB):
    pilot = await Repository(db).require(m.Pilot, pilot_id, lock=True)
    owned(actor, pilot.user_id)
    if not pilot.verified:
        raise BusinessError("unverified_pilot", "Pilot verification is required", 403)
    if pilot.state == "suspended":
        raise BusinessError("pilot_unavailable", "Suspended pilots cannot change availability", 403)
    if body.available:
        Incident = F["operations.operational_incidents"]
        unresolved_safety_report = await db.scalar(
            select(Incident.id)
            .where(
                Incident.pilot_id == pilot.id,
                Incident.safety_emergency.is_(True),
                Incident.status.in_(["open", "acknowledged"]),
            )
            .limit(1)
        )
        if unresolved_safety_report:
            raise BusinessError(
                "incident_review_pending",
                "Operations must resolve the safety report before you can go online",
                409,
            )
        if not pilot.location_consent_at:
            raise BusinessError(
                "location_consent_required",
                "Accept the location policy before going online",
                403,
            )
        latest = await db.scalar(
            select(m.LatestLocation).where(m.LatestLocation.pilot_id == pilot.id)
        )
        if not latest or latest.observed_at < now() - timedelta(seconds=90):
            raise BusinessError(
                "fresh_location_required", "Submit current location before going online", 409
            )
    else:
        active = await db.scalar(
            select(m.Assignment.id)
            .where(
                m.Assignment.pilot_id == pilot.id,
                m.Assignment.status.in_(["offered", "accepted", "picked_up"]),
            )
            .limit(1)
        )
        if active:
            raise BusinessError(
                "active_assignment",
                "Reject open offers or complete/reassign active deliveries before going offline",
                409,
            )
    pilot.available = body.available
    pilot.state = "online_available" if body.available else "offline"
    return pilot


@router.post("/pilots/me/availability", response_model=s.IdOut, tags=["Fulfillment"])
async def my_availability(body: s.PilotAvailabilityIn, actor: Actor, db: DB):
    pilot = await db.scalar(
        select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)).with_for_update()
    )
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    if not pilot.verified or pilot.state == "suspended":
        raise BusinessError(
            "pilot_unavailable", "Pilot is not eligible to change availability", 403
        )
    if body.state == "online_available":
        Incident = F["operations.operational_incidents"]
        unresolved_safety_report = await db.scalar(
            select(Incident.id)
            .where(
                Incident.pilot_id == pilot.id,
                Incident.safety_emergency.is_(True),
                Incident.status.in_(["open", "acknowledged"]),
            )
            .limit(1)
        )
        if unresolved_safety_report:
            raise BusinessError(
                "incident_review_pending",
                "Operations must resolve the safety report before you can go online",
                409,
            )
        if not pilot.location_consent_at:
            raise BusinessError(
                "location_consent_required",
                "Accept the location policy before going online",
                403,
            )
        latest = await db.scalar(
            select(m.LatestLocation).where(m.LatestLocation.pilot_id == pilot.id)
        )
        if not latest or latest.observed_at < now() - timedelta(seconds=90):
            raise BusinessError(
                "fresh_location_required", "Submit a current location before going online", 409
            )
        pilot.available = True
    else:
        if body.state in {"offline", "on_break"}:
            # Do not clear presence or start a break while a pending offer or work item
            # still expects this pilot's response. A distinct unavailable state remains
            # available for operational exceptions while preserving assignment ownership.
            active = await db.scalar(
                select(m.Assignment.id)
                .where(
                    m.Assignment.pilot_id == pilot.id,
                    m.Assignment.status.in_(["offered", "accepted", "picked_up"]),
                )
                .limit(1)
            )
            if active:
                raise BusinessError(
                    "active_assignment",
                    "Reject open offers or complete/reassign work before going offline "
                    "or taking a break",
                    409,
                )
        pilot.available = False
    pilot.state = body.state
    return pilot


@router.get("/pilots/me", tags=["Fulfillment"])
async def my_pilot_profile(actor: Actor, db: DB):
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    return {
        "id": pilot.id,
        "city_id": pilot.city_id,
        "verified": pilot.verified,
        "state": pilot.state,
        "available": pilot.available,
        "vehicle_type": pilot.vehicle_type,
        "max_active_tasks": pilot.max_active_tasks,
        "location_consent": pilot.location_consent_at is not None,
    }


@router.get("/pilots/me/assignments", tags=["Fulfillment"])
async def my_pilot_assignments(actor: Actor, db: DB, limit: Limit = 50):
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    rows = (
        await db.execute(
            select(
                m.Assignment,
                m.DeliveryTask,
                m.FulfillmentUnit,
                m.MerchantOrder,
                m.Branch,
                m.Brand,
                m.Window,
            )
            .join(m.DeliveryTask, m.Assignment.task_id == m.DeliveryTask.id)
            .join(m.FulfillmentUnit, m.DeliveryTask.fulfillment_unit_id == m.FulfillmentUnit.id)
            .join(m.MerchantOrder, m.FulfillmentUnit.merchant_order_id == m.MerchantOrder.id)
            .join(m.Branch, m.MerchantOrder.branch_id == m.Branch.id)
            .join(m.Brand, m.Branch.brand_id == m.Brand.id)
            .join(m.Window, m.FulfillmentUnit.window_id == m.Window.id)
            .where(
                m.Assignment.pilot_id == pilot.id,
                m.Assignment.status.in_(["offered", "accepted", "picked_up"]),
            )
            .order_by(m.Assignment.expires_at, m.Assignment.created_at, m.Assignment.id)
            .limit(limit)
        )
    ).all()
    child_ids = {child.id for _, _, _, child, _, _, _ in rows}
    item_rows = (
        (
            await db.scalars(
                select(m.OrderItem)
                .where(m.OrderItem.merchant_order_id.in_(child_ids))
                .order_by(m.OrderItem.created_at, m.OrderItem.id)
            )
        ).all()
        if child_ids
        else []
    )
    items_by_child = {}
    for item in item_rows:
        items_by_child.setdefault(item.merchant_order_id, []).append(
            {
                "name": item.product_name,
                "variant": item.variant_name,
                "quantity": item.quantity,
                "unit": item.unit,
            }
        )
    return {
        "pilot": {
            "id": pilot.id,
            "city_id": pilot.city_id,
            "state": pilot.state,
            "verified": pilot.verified,
            "available": pilot.available,
        },
        "items": [
            {
                "assignment_id": assignment.id,
                "assignment_status": assignment.status,
                "expires_at": assignment.expires_at,
                "delivery_task_id": task.id,
                "task_status": task.status,
                "task_version": task.version,
                "merchant_order_status": child.status,
                "order_reference": str(child.order_id).split("-")[0].upper(),
                "merchant_order_id": child.id,
                "merchant_name": branch.name,
                "merchant_type": brand.merchant_type,
                "delivery_method": unit.delivery_method,
                "pickup": {
                    "name": branch.name,
                    "latitude": str(branch.latitude),
                    "longitude": str(branch.longitude),
                },
                # Exact customer address is disclosed only after assignment acceptance.
                "dropoff": unit.address_snapshot
                if assignment.status in {"accepted", "picked_up"}
                else None,
                "window_starts_at": window.starts_at,
                "window_ends_at": window.ends_at,
                "order_items": items_by_child.get(child.id, []),
            }
            for assignment, task, unit, child, branch, brand, window in rows
        ],
    }


@router.get("/pilots/me/earnings", tags=["Finance"])
async def my_pilot_earnings(actor: Actor, db: DB, limit: Limit = 100):
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    Earning, Currency = F["fulfillment.pilot_earnings"], m.Currency
    rows = (
        await db.execute(
            select(Earning, Currency.code)
            .join(Currency, Earning.currency_id == Currency.id)
            .where(Earning.pilot_id == pilot.id)
            .order_by(Earning.created_at.desc(), Earning.id.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": earning.id,
                "task_id": earning.task_id,
                "amount": earning.amount,
                "currency": currency,
                "recorded_at": earning.created_at,
            }
            for earning, currency in rows
        ],
        "authoritative_source": "fulfillment.pilot_earnings",
        "payout_status": "not_exposed_by_current_api",
    }


@router.get("/pilots/me/operations", tags=["Fulfillment"])
async def my_pilot_operations(actor: Actor, db: DB):
    """Return only the authenticated pilot's shift, capabilities, and service zones."""
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    instant = now()
    Shift = F["fulfillment.pilot_shifts"]
    shift = await db.scalar(
        select(Shift)
        .where(Shift.pilot_id == pilot.id, Shift.ends_at > instant)
        .order_by(Shift.starts_at, Shift.id)
        .limit(1)
    )
    ServiceZone = F["fulfillment.pilot_service_zones"]
    zones = (
        await db.execute(
            select(m.Zone.id, m.Zone.name)
            .join(ServiceZone, ServiceZone.zone_id == m.Zone.id)
            .where(
                ServiceZone.pilot_id == pilot.id,
                m.Zone.city_id == pilot.city_id,
                m.Zone.active.is_(True),
            )
            .order_by(m.Zone.name, m.Zone.id)
            .limit(20)
        )
    ).all()
    Capability = F["fulfillment.pilot_capabilities"]
    capabilities = (
        await db.scalars(
            select(Capability.capability)
            .where(
                Capability.pilot_id == pilot.id,
                or_(Capability.expires_at.is_(None), Capability.expires_at > instant),
            )
            .order_by(Capability.capability)
        )
    ).all()
    remaining = (
        max(0, int((shift.ends_at - instant).total_seconds() // 60))
        if shift and shift.starts_at <= instant
        else None
    )
    return {
        "pilot_id": pilot.id,
        "city_id": pilot.city_id,
        "vehicle_type": pilot.vehicle_type,
        "capabilities": list(capabilities),
        "shift": (
            {
                "starts_at": shift.starts_at,
                "ends_at": shift.ends_at,
                "status": "active" if shift.starts_at <= instant else "upcoming",
                "remaining_minutes": remaining,
            }
            if shift
            else None
        ),
        "authorized_zones": [{"id": zone_id, "name": name} for zone_id, name in zones],
        "breaks": "not_configured",
        "schedule_authority": "fulfillment.pilot_shifts",
    }


@router.get("/pilots/me/supply-demand", tags=["Fulfillment"])
async def my_pilot_supply_demand(actor: Actor, db: DB):
    """Provide coarse, advisory demand signals for only the pilot's authorized zones."""
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    city = await Repository(db).require(m.City, pilot.city_id)
    ServiceZone = F["fulfillment.pilot_service_zones"]
    zones = (
        await db.execute(
            select(m.Zone.id, m.Zone.name)
            .join(ServiceZone, ServiceZone.zone_id == m.Zone.id)
            .where(
                ServiceZone.pilot_id == pilot.id,
                m.Zone.city_id == pilot.city_id,
                m.Zone.active.is_(True),
            )
            .order_by(m.Zone.name, m.Zone.id)
            .limit(5)
        )
    ).all()
    Forecast = F["intelligence.ai_forecast_outputs"]
    signals = []
    for zone_id, name in zones:
        cached = await db.scalar(
            select(Forecast)
            .where(
                Forecast.zone_id == zone_id,
                Forecast.expires_at > now(),
            )
            .order_by(Forecast.source_cutoff.desc(), Forecast.id.desc())
            .limit(1)
        )
        forecast = (
            cached.forecast
            if cached
            else await ai_service.city_demand_forecast(db, city, zone_id=zone_id)
        )
        if not cached:
            await add(
                db,
                Forecast,
                city_id=city.id,
                zone_id=zone_id,
                interval_minutes=60,
                forecast=forecast,
                provenance=forecast["provenance"],
                feature_schema_version=forecast["feature_schema_version"],
                source_cutoff=now(),
                expires_at=now() + timedelta(minutes=15),
            )
            await ai_service.log_prediction(
                db,
                "demand",
                actor.subject,
                "pilot_zone_demand_signal",
                {"zone_id": str(zone_id)},
                {"model_status": forecast["model_status"]},
            )
        model_status = forecast.get("model_status", "unknown")
        expected = forecast.get("horizons", {}).get("next_1_hour")
        if model_status == "cold_start_fallback" or expected is None:
            band = "insufficient_history"
            recommendation = "No reliable demand history is available for this zone yet."
        elif expected >= 4:
            band = "high"
            recommendation = "Higher demand is forecast; repositioning is optional."
        elif expected >= 1:
            band = "moderate"
            recommendation = "Some demand is forecast; repositioning is optional."
        else:
            band = "low"
            recommendation = "Demand is forecast to be quieter."
        signals.append(
            {
                "zone_id": zone_id,
                "zone_name": name,
                "window": "next_hour",
                "signal_type": "prediction",
                "demand_band": band,
                "recommendation": recommendation,
                "generated_at": forecast.get("generated_at"),
                "model_status": model_status,
                "provenance": forecast.get("provenance", "unknown"),
            }
        )
    return {
        "city_id": pilot.city_id,
        "signals": signals,
        "pilot_supply": "zone_level_supply_unavailable",
        "advisory_only": True,
        "limitations": (
            "No zone-level pilot supply, travel-time recommendation, incentives, "
            "or trained demand model is configured."
        ),
    }


@router.post("/pilots/me/incidents", status_code=201, tags=["Fulfillment"])
async def report_pilot_incident(body: s.PilotIncidentIn, actor: Actor, request: Request, db: DB):
    """Persist a pilot safety/operations report in the shared incident ledger."""
    pilot = await db.scalar(
        select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)).with_for_update()
    )
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    if body.delivery_task_id:
        task = await Repository(db).require(m.DeliveryTask, body.delivery_task_id)
        assignment = await db.scalar(
            select(m.Assignment.id)
            .where(
                m.Assignment.task_id == task.id,
                m.Assignment.pilot_id == pilot.id,
                m.Assignment.status.in_(["accepted", "picked_up"]),
            )
            .limit(1)
        )
        if not assignment:
            raise BusinessError("incident_task_forbidden", "Task is not active for this pilot", 403)
        _task, _unit, _child, branch = await logistics.task_context(db, task.id)
        if branch.city_id != pilot.city_id:
            raise BusinessError("incident_task_forbidden", "Task is outside the pilot city", 403)

    critical_categories = {"accident", "medical_emergency"}
    high_categories = {
        "vehicle_breakdown",
        "road_blockage",
        "unsafe_pickup_area",
        "unsafe_delivery_area",
        "severe_weather",
    }
    must_stop = body.safety_emergency or body.category in critical_categories | high_categories
    severity = (
        "critical"
        if body.safety_emergency or body.category in critical_categories
        else ("high" if body.category in high_categories else "normal")
    )
    Incident = F["operations.operational_incidents"]
    incident = await add(
        db,
        Incident,
        city_id=pilot.city_id,
        pilot_id=pilot.id,
        delivery_task_id=body.delivery_task_id,
        reporter_id=UUID(actor.subject),
        category=body.category,
        severity=severity,
        summary=body.summary,
        status="open",
        safety_emergency=must_stop,
    )
    if must_stop and pilot.state != "suspended":
        pilot.available = False
        pilot.state = "unavailable"
    await audit(
        db,
        actor,
        "pilot_incident.create",
        incident.id,
        request.state.request_id,
        current="open",
    )
    await event(
        db,
        "pilot.incident_reported",
        incident.id,
        request.state.request_id,
        pilot_id=pilot.id,
        reporter_id=actor.subject,
        city_id=pilot.city_id,
        severity=severity,
    )
    return {
        "id": incident.id,
        "status": incident.status,
        "category": incident.category,
        "severity": incident.severity,
        "safety_emergency": incident.safety_emergency,
        "created_at": incident.created_at,
        "next_step": (
            "Do not accept new work. Move to safety and contact local emergency services "
            "if you are in immediate danger. The report is saved for operations review; "
            "staff must resolve it before you can go online again."
            if must_stop
            else "The incident report is saved for operations review."
        ),
    }


@router.get("/pilots/me/incidents", tags=["Fulfillment"])
async def my_pilot_incidents(actor: Actor, db: DB, limit: Limit = 50):
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    Incident = F["operations.operational_incidents"]
    rows = (
        await db.scalars(
            select(Incident)
            .where(
                Incident.pilot_id == pilot.id,
                Incident.reporter_id == UUID(actor.subject),
            )
            .order_by(Incident.created_at.desc(), Incident.id.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "delivery_task_id": row.delivery_task_id,
                "category": row.category,
                "severity": row.severity,
                "status": row.status,
                "safety_emergency": row.safety_emergency,
                "summary": row.summary,
                "resolution_summary": row.resolution_summary,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.post("/pilots/me/location-consent", tags=["Fulfillment"])
async def pilot_location_consent(body: s.LocationConsentIn, actor: Actor, request: Request, db: DB):
    pilot = await db.scalar(
        select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)).with_for_update()
    )
    if not pilot:
        raise BusinessError("pilot_profile_required", "Create a pilot profile first", 403)
    recorded_at = now()
    pilot.location_consent_at = recorded_at if body.accepted else None
    pilot.location_consent_version = body.policy_version if body.accepted else None
    if not body.accepted:
        pilot.available, pilot.state = False, "offline"
    await add(
        db,
        F["fulfillment.pilot_location_consents"],
        pilot_id=pilot.id,
        policy_version=body.policy_version,
        accepted=body.accepted,
    )
    await db.commit()
    if not body.accepted:
        try:
            await tracking.clear_cached_presence(request.app.state.redis, pilot.id, pilot.city_id)
        except Exception:
            pass
    return {
        "pilot_id": pilot.id,
        "accepted": body.accepted,
        "policy_version": body.policy_version,
        "recorded_at": recorded_at,
    }


@router.post("/pilots/me/location", tags=["Fulfillment"])
async def my_location(body: s.LocationIn, actor: Actor, request: Request, db: DB):
    db.info["settings"] = request.app.state.settings
    result = await tracking.ingest_location(db, actor, body, request.app.state.settings)
    if result["accepted"]:
        await db.commit()
        loop = asyncio.get_running_loop()
        retry_after = getattr(request.app.state, "redis_retry_after", 0)
        in_cooldown = loop.time() < retry_after
        try:
            if in_cooldown:
                raise ConnectionError("Redis tracking cache is in cooldown")
            await tracking.cache_location(
                request.app.state.redis,
                result,
                body,
                request.app.state.settings.pilot_location_fresh_seconds * 2,
            )
            result["cache_status"] = "ok"
            active = (
                await db.execute(
                    select(m.Assignment, m.DeliveryTask, m.FulfillmentUnit, m.MerchantOrder)
                    .join(m.DeliveryTask, m.Assignment.task_id == m.DeliveryTask.id)
                    .join(
                        m.FulfillmentUnit,
                        m.DeliveryTask.fulfillment_unit_id == m.FulfillmentUnit.id,
                    )
                    .join(
                        m.MerchantOrder, m.FulfillmentUnit.merchant_order_id == m.MerchantOrder.id
                    )
                    .where(
                        m.Assignment.pilot_id == UUID(result["pilot_id"]),
                        m.Assignment.status.in_(["accepted", "picked_up"]),
                        m.DeliveryTask.status.in_(["assigned", "picked_up"]),
                    )
                )
            ).all()
            for _assignment, task, _unit, child in active:
                coalesce_key = f"quickbuddy:tracking:coalesce:{task.id}"
                if await request.app.state.redis.set(coalesce_key, "1", nx=True, ex=5):
                    await publish(
                        request.app.state.redis,
                        f"order:{child.order_id}",
                        {
                            "event_type": "pilot.location",
                            "delivery_id": str(task.id),
                            "latitude": str(body.latitude),
                            "longitude": str(body.longitude),
                            "observed_at": body.observed_at.isoformat(),
                            "accuracy_m": str(body.accuracy_m),
                        },
                    )
        except Exception:
            if not in_cooldown:
                request.app.state.redis_retry_after = loop.time() + 5
            result["cache_status"] = "degraded"
    return result


@router.get("/orders/{order_id}/tracking", tags=["Tracking"])
async def order_tracking(order_id: UUID, actor: Actor, request: Request, db: DB):
    order = await Repository(db).require(m.Order, order_id)
    owned(actor, order.user_id)
    tasks = (
        await db.execute(
            select(m.DeliveryTask, m.FulfillmentUnit, m.MerchantOrder)
            .join(m.FulfillmentUnit, m.DeliveryTask.fulfillment_unit_id == m.FulfillmentUnit.id)
            .join(m.MerchantOrder, m.FulfillmentUnit.merchant_order_id == m.MerchantOrder.id)
            .where(m.MerchantOrder.order_id == order.id)
            .order_by(m.DeliveryTask.id)
        )
    ).all()
    task_ids = [task.id for task, _, _ in tasks]
    # One joined read instead of two round trips for every merchant delivery.
    live_locations = (
        (
            await db.execute(
                select(m.Assignment.task_id, m.LatestLocation)
                .join(m.Pilot, m.Pilot.id == m.Assignment.pilot_id)
                .join(m.User, m.User.id == m.Pilot.user_id)
                .join(m.LatestLocation, m.LatestLocation.pilot_id == m.Pilot.id)
                .where(
                    m.Assignment.task_id.in_(task_ids),
                    m.Assignment.status.in_(["accepted", "picked_up"]),
                    m.Pilot.location_consent_at.is_not(None),
                    m.Pilot.verified.is_(True),
                    m.Pilot.state.not_in(["offline", "suspended"]),
                    m.User.status == "active",
                    m.LatestLocation.observed_at
                    >= now()
                    - timedelta(seconds=request.app.state.settings.pilot_location_fresh_seconds),
                )
            )
        ).all()
        if task_ids
        else []
    )
    locations_by_task = {task_id: latest for task_id, latest in live_locations}
    items = []
    for task, unit, child in tasks:
        latest = locations_by_task.get(task.id)
        location = None
        if latest and task.status in {"assigned", "picked_up"}:
            location = {
                "latitude": str(latest.latitude),
                "longitude": str(latest.longitude),
                "observed_at": latest.observed_at,
                "accuracy_m": str(latest.accuracy_m),
                "valid_until": latest.observed_at
                + timedelta(seconds=request.app.state.settings.pilot_location_fresh_seconds),
            }
        items.append(
            {
                "delivery_id": str(task.id),
                "merchant_order_id": str(child.id),
                "status": task.status,
                "version": task.version,
                "delivery_method": unit.delivery_method,
                "pilot_location": location,
            }
        )
    return {"order_id": str(order.id), "generated_at": now(), "deliveries": items}


@router.get("/deliveries/{delivery_id}", tags=["Tracking"])
async def delivery_snapshot(delivery_id: UUID, actor: Actor, db: DB):
    task, unit, child, branch = await logistics.task_context(db, delivery_id)
    order = await Repository(db).require(m.Order, child.order_id)
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    assigned_to_actor = bool(
        pilot
        and await db.scalar(
            select(m.Assignment.id)
            .where(
                m.Assignment.task_id == task.id,
                m.Assignment.pilot_id == pilot.id,
            )
            .limit(1)
        )
    )
    allowed = order.user_id == UUID(actor.subject) or assigned_to_actor
    if not allowed:
        await branch_scope(db, actor, branch.id, "dispatch.write")
    return {
        "delivery_id": str(task.id),
        "status": task.status,
        "version": task.version,
        "merchant_order_id": str(child.id),
        "branch_id": str(branch.id),
        "delivery_method": unit.delivery_method,
        "address": unit.address_snapshot if order.user_id == UUID(actor.subject) else None,
    }


@router.get("/deliveries/{delivery_id}/timeline", tags=["Tracking"])
async def delivery_timeline(delivery_id: UUID, actor: Actor, db: DB):
    task, unit, child, branch = await logistics.task_context(db, delivery_id)
    order = await Repository(db).require(m.Order, child.order_id)
    pilot = await db.scalar(select(m.Pilot).where(m.Pilot.user_id == UUID(actor.subject)))
    assigned_to_actor = bool(
        pilot
        and await db.scalar(
            select(m.Assignment.id)
            .where(
                m.Assignment.task_id == task.id,
                m.Assignment.pilot_id == pilot.id,
            )
            .limit(1)
        )
    )
    if order.user_id != UUID(actor.subject) and not assigned_to_actor:
        await branch_scope(db, actor, branch.id, "dispatch.write")
    model = F["fulfillment.dispatch_events"]
    events = (
        await db.execute(
            select(model.event_type, model.created_at)
            .where(model.task_id == task.id)
            .order_by(model.created_at, model.id)
        )
    ).all()
    return {
        "delivery_id": str(task.id),
        "status": task.status,
        "events": [{"event": event, "at": at} for event, at in events],
    }


@router.get("/deliveries/{delivery_id}/eta", tags=["Tracking"])
async def delivery_eta(delivery_id: UUID, actor: Actor, request: Request, db: DB):
    task, unit, child, branch = await logistics.task_context(db, delivery_id)
    await delivery_snapshot(delivery_id, actor, db)
    return await eta_engine.estimate(
        db,
        task,
        unit,
        child,
        branch,
        request.app.state.routing_provider,
        request.app.state.settings,
    )


@router.post(
    "/realtime/tickets", response_model=s.TrackingTicketOut, status_code=201, tags=["Realtime"]
)
async def realtime_ticket(actor: Actor, request: Request, db: DB):
    raw, token_hash, ticket_id = tracking.issue_ticket()
    expires = now() + timedelta(
        seconds=request.app.state.settings.tracking_websocket_ticket_seconds
    )
    await add(
        db,
        F["fulfillment.tracking_ws_tickets"],
        id=ticket_id,
        user_id=UUID(actor.subject),
        token_hash=token_hash,
        expires_at=expires,
        consumed_at=None,
    )
    return {"ticket": raw, "expires_at": expires}


@router.put("/pilots/{pilot_id}/location", response_model=s.IdOut, tags=["Fulfillment"])
async def location(pilot_id: UUID, body: s.LocationIn, actor: Actor, request: Request, db: DB):
    pilot = await Repository(db).require(m.Pilot, pilot_id)
    owned(actor, pilot.user_id)
    db.info["settings"] = request.app.state.settings
    result = await tracking.ingest_location(db, actor, body, request.app.state.settings)
    if result["accepted"]:
        await db.commit()
        try:
            await tracking.cache_location(
                request.app.state.redis,
                result,
                body,
                request.app.state.settings.pilot_location_fresh_seconds * 2,
            )
        except Exception:
            pass
    return result


@router.post(
    "/delivery-tasks/{task_id}/offer",
    response_model=s.AssignmentOut,
    status_code=201,
    tags=["Fulfillment"],
)
async def offer(task_id: UUID, body: s.OfferIn, actor: Actor, request: Request, db: DB):
    return await logistics.offer(db, actor, task_id, body.pilot_id, request.state.request_id)


@router.post(
    "/pilot-assignments/{assignment_id}/accept", response_model=s.VersionOut, tags=["Fulfillment"]
)
async def accept(assignment_id: UUID, actor: Actor, request: Request, db: DB):
    return await logistics.accept(db, actor, assignment_id, request.state.request_id)


@router.post("/pilot-assignments/{assignment_id}/reject", tags=["Fulfillment"])
async def reject_assignment(assignment_id: UUID, actor: Actor, request: Request, db: DB):
    task = await logistics.reject_offer(db, actor, assignment_id, request.state.request_id)
    return {"id": task.id, "status": task.status, "version": task.version}


@router.get("/operations/cities/{city_id}/pilot-incidents", tags=["Dispatch operations"])
async def city_pilot_incidents(
    city_id: UUID, actor: Actor, request: Request, db: DB, limit: Limit = 50
):
    city = await Repository(db).require(m.City, city_id)
    await scoped(db, actor, "dispatch.write", city_id=city.id)
    Incident = F["operations.operational_incidents"]
    rows = (
        await db.scalars(
            select(Incident)
            .where(Incident.city_id == city.id, Incident.reporter_id.is_not(None))
            .order_by(Incident.created_at.desc(), Incident.id.desc())
            .limit(limit)
        )
    ).all()
    for row in rows:
        await audit(db, actor, "pilot_incident.read", row.id, request.state.request_id)
    return {
        "items": [
            {
                "id": row.id,
                "pilot_id": row.pilot_id,
                "delivery_task_id": row.delivery_task_id,
                "category": row.category,
                "severity": row.severity,
                "status": row.status,
                "safety_emergency": row.safety_emergency,
                "summary": row.summary,
                "resolution_summary": row.resolution_summary,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }


@router.post("/operations/pilot-incidents/{incident_id}/acknowledge", tags=["Dispatch operations"])
async def acknowledge_pilot_incident(incident_id: UUID, actor: Actor, request: Request, db: DB):
    Incident = F["operations.operational_incidents"]
    incident = await db.scalar(select(Incident).where(Incident.id == incident_id).with_for_update())
    if not incident or incident.reporter_id is None:
        raise BusinessError("incident_not_found", "Pilot incident was not found", 404)
    await scoped(db, actor, "dispatch.write", city_id=incident.city_id)
    if incident.status == "acknowledged":
        return {"id": incident.id, "status": incident.status}
    if incident.status != "open":
        raise BusinessError("incident_not_open", "Only open incidents can be acknowledged", 409)
    incident.status = "acknowledged"
    await audit(
        db,
        actor,
        "pilot_incident.acknowledge",
        incident.id,
        request.state.request_id,
        previous="open",
        current="acknowledged",
    )
    await event(
        db,
        "pilot.incident_acknowledged",
        incident.id,
        request.state.request_id,
        city_id=incident.city_id,
        pilot_id=incident.pilot_id,
    )
    return {"id": incident.id, "status": incident.status}


@router.post("/operations/pilot-incidents/{incident_id}/resolve", tags=["Dispatch operations"])
async def resolve_pilot_incident(
    incident_id: UUID,
    body: s.PilotIncidentResolveIn,
    actor: Actor,
    request: Request,
    db: DB,
):
    Incident = F["operations.operational_incidents"]
    incident = await db.scalar(select(Incident).where(Incident.id == incident_id).with_for_update())
    if not incident or incident.reporter_id is None:
        raise BusinessError("incident_not_found", "Pilot incident was not found", 404)
    await scoped(db, actor, "dispatch.write", city_id=incident.city_id)
    if incident.status == "resolved":
        return {"id": incident.id, "status": incident.status}
    if incident.status != "acknowledged":
        raise BusinessError(
            "incident_not_acknowledged",
            "Acknowledge the incident before resolving",
            409,
        )
    incident.status = "resolved"
    incident.resolution_summary = body.resolution_summary
    await audit(
        db,
        actor,
        "pilot_incident.resolve",
        incident.id,
        request.state.request_id,
        previous="acknowledged",
        current="resolved",
    )
    await event(
        db,
        "pilot.incident_resolved",
        incident.id,
        request.state.request_id,
        city_id=incident.city_id,
        pilot_id=incident.pilot_id,
    )
    return {"id": incident.id, "status": incident.status}


@router.get("/operations/cities/{city_id}/dispatch", tags=["Dispatch operations"])
async def city_dispatch(
    city_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    await scoped(db, actor, "dispatch.write", city_id=city_id)
    predicates = [
        m.Branch.city_id == city_id,
        m.DeliveryTask.status.in_(["unassigned", "offered", "assigned", "picked_up"]),
    ]
    tasks, next_id = await Repository(db).page(
        m.DeliveryTask,
        [
            m.DeliveryTask.id.in_(
                select(m.DeliveryTask.id)
                .join(m.FulfillmentUnit, m.DeliveryTask.fulfillment_unit_id == m.FulfillmentUnit.id)
                .join(m.MerchantOrder, m.FulfillmentUnit.merchant_order_id == m.MerchantOrder.id)
                .join(m.Branch, m.MerchantOrder.branch_id == m.Branch.id)
                .where(*predicates)
            )
        ],
        after=decode_cursor(cursor),
        limit=limit,
    )
    counts = {}
    for status in ("unassigned", "offered", "assigned", "picked_up"):
        counts[status] = await db.scalar(
            select(func.count())
            .select_from(m.DeliveryTask)
            .join(m.FulfillmentUnit)
            .join(m.MerchantOrder)
            .join(m.Branch)
            .where(m.Branch.city_id == city_id, m.DeliveryTask.status == status)
        )
    return {
        "city_id": city_id,
        "counts": counts,
        "tasks": [{"id": row.id, "status": row.status, "version": row.version} for row in tasks],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.get("/operations/cities/{city_id}/fleet", tags=["Dispatch operations"])
async def city_fleet(city_id: UUID, actor: Actor, db: DB):
    await scoped(db, actor, "dispatch.write", city_id=city_id)
    counts = {}
    for state_name in (
        "offline",
        "online_available",
        "offer_pending",
        "assigned",
        "on_break",
        "unavailable",
        "suspended",
    ):
        counts[state_name] = await db.scalar(
            select(func.count())
            .select_from(m.Pilot)
            .where(
                m.Pilot.city_id == city_id,
                m.Pilot.state == state_name,
                m.Pilot.verified.is_(True),
            )
        )
    return {"city_id": city_id, "counts": counts, "generated_at": now()}


@router.get("/ai/demand/cities/{city_id}/forecast", tags=["AI intelligence"])
async def ai_city_forecast(city_id: UUID, actor: Actor, db: DB):
    city = await Repository(db).require(m.City, city_id)
    await scoped(db, actor, "ai.read", city_id=city.id)
    result = await ai_service.city_demand_forecast(db, city)
    await add(
        db,
        F["intelligence.ai_feature_pipeline_runs"],
        feature_schema_version=result["feature_schema_version"],
        source_cutoff=now(),
        row_count=result["sample_count"],
        quality=result["data_quality"],
        status="succeeded",
    )
    await add(
        db,
        F["intelligence.ai_forecast_outputs"],
        city_id=city.id,
        zone_id=None,
        interval_minutes=1440,
        forecast=result,
        provenance=result["provenance"],
        feature_schema_version=result["feature_schema_version"],
        source_cutoff=now(),
        expires_at=now() + timedelta(minutes=15),
    )
    await ai_service.log_prediction(
        db, "demand", actor.subject, "city_demand_forecast", {"city_id": str(city.id)}, result
    )
    return result


@router.get("/ai/demand/zones/{zone_id}/forecast", tags=["AI intelligence"])
async def ai_zone_forecast(zone_id: UUID, actor: Actor, db: DB):
    zone = await Repository(db).require(m.Zone, zone_id)
    if not zone.active:
        raise BusinessError("zone_unavailable", "Service zone is inactive", 409)
    city = await Repository(db).require(m.City, zone.city_id)
    await scoped(db, actor, "ai.read", city_id=city.id)
    result = await ai_service.city_demand_forecast(db, city, zone_id=zone.id)
    result["scope"] = "mapped_merchant_service_areas"
    await add(
        db,
        F["intelligence.ai_forecast_outputs"],
        city_id=city.id,
        zone_id=zone.id,
        interval_minutes=1440,
        forecast=result,
        provenance=result["provenance"],
        feature_schema_version=result["feature_schema_version"],
        source_cutoff=now(),
        expires_at=now() + timedelta(minutes=15),
    )
    await ai_service.log_prediction(
        db, "demand", actor.subject, "zone_demand_forecast", {"zone_id": str(zone.id)}, result
    )
    return result


@router.post("/ai/preparation/predict", tags=["AI intelligence"])
async def ai_preparation_predict(body: s.PreparationPredictIn, actor: Actor, db: DB):
    branch = await Repository(db).require(m.Branch, body.branch_id)
    await scoped(db, actor, "ai.read", branch.organization_id, branch.city_id, branch.id)
    queue_depth = await db.scalar(
        select(func.count())
        .select_from(m.MerchantOrder)
        .where(
            m.MerchantOrder.branch_id == branch.id,
            m.MerchantOrder.status.in_(["accepted", "preparing"]),
            m.MerchantOrder.created_at <= now(),
        )
    )
    result = ai_service.preparation_rule(body.item_count, int(queue_depth or 0))
    result["features"] = {
        "item_count": body.item_count,
        "merchant_queue_depth": int(queue_depth or 0),
        "event_at": now().isoformat(),
        "availability_at": now().isoformat(),
    }
    await ai_service.log_prediction(
        db,
        "preparation",
        actor.subject,
        "preparation_duration",
        {"branch_id": str(branch.id), **result["features"]},
        result,
        branch.organization_id,
    )
    return result


@router.get("/ai/positioning/zones/{zone_id}/recommendations", tags=["AI intelligence"])
async def ai_positioning(zone_id: UUID, actor: Actor, db: DB):
    zone = await Repository(db).require(m.Zone, zone_id)
    if not zone.active:
        raise BusinessError("zone_unavailable", "Service zone is inactive", 409)
    city = await Repository(db).require(m.City, zone.city_id)
    await scoped(db, actor, "ai.read", city_id=city.id)
    forecast = await ai_service.city_demand_forecast(db, city, zone_id=zone.id)
    settings = getattr(db, "info", {}).get("settings")
    freshness = getattr(settings, "pilot_location_fresh_seconds", 90)
    available = await db.scalar(
        select(func.count())
        .select_from(m.Pilot)
        .join(m.LatestLocation, m.LatestLocation.pilot_id == m.Pilot.id)
        .where(
            m.Pilot.city_id == city.id,
            m.Pilot.verified.is_(True),
            m.Pilot.available.is_(True),
            m.Pilot.state.in_(["online_available", "assigned"]),
            m.Pilot.location_consent_at.is_not(None),
            m.LatestLocation.observed_at >= now() - timedelta(seconds=freshness),
        )
    )
    shortage = forecast["horizons"]["next_1_hour"] > 0 and (available or 0) == 0
    result = {
        "city_id": str(city.id),
        "zone_id": str(zone.id),
        "expected_orders_next_hour": forecast["horizons"]["next_1_hour"],
        "available_pilots_citywide": int(available or 0),
        "zone_level_pilot_supply": "unavailable",
        "recommendation": (
            "Review voluntary pilot supply options for this zone; no automatic relocation."
            if shortage
            else "No citywide pilot shortage is indicated by the available baseline."
        ),
        "provenance": "deterministic_rule",
        "model_status": "untrained_baseline",
        "limitations": "pilot profiles are city-scoped; current zone presence is not persisted",
    }
    await ai_service.log_prediction(
        db,
        "demand",
        actor.subject,
        "pilot_positioning_recommendation",
        {"zone_id": str(zone.id)},
        result,
    )
    return result


@router.post("/ai/dispatch/recommend", tags=["AI intelligence"])
@router.post("/ai/dispatch/optimize", tags=["AI intelligence"])
async def ai_dispatch_optimize(body: s.DispatchOptimizeIn, actor: Actor, request: Request, db: DB):
    await actor_budget(request, actor, "ai-dispatch", 30)
    if len(set(body.task_ids)) != len(body.task_ids):
        raise BusinessError("duplicate_task", "Task list must contain unique IDs", 422)
    await scoped(db, actor, "ai.read", city_id=body.city_id)
    selected_tasks = (
        await db.execute(
            select(m.DeliveryTask, m.FulfillmentUnit, m.MerchantOrder, m.Branch)
            .join(m.FulfillmentUnit, m.DeliveryTask.fulfillment_unit_id == m.FulfillmentUnit.id)
            .join(m.MerchantOrder, m.FulfillmentUnit.merchant_order_id == m.MerchantOrder.id)
            .join(m.Branch, m.MerchantOrder.branch_id == m.Branch.id)
            .where(
                m.DeliveryTask.id.in_(body.task_ids),
                m.DeliveryTask.status == "unassigned",
                m.Branch.city_id == body.city_id,
                m.MerchantOrder.status.in_(["accepted", "preparing", "ready"]),
                m.FulfillmentUnit.delivery_method != "pickup",
            )
            .limit(50)
        )
    ).all()
    if len(selected_tasks) != len(body.task_ids):
        raise BusinessError(
            "tasks_unavailable", "One or more tasks are not assignable in this city", 409
        )
    settings = getattr(db, "info", {}).get("settings")
    freshness = getattr(settings, "pilot_location_fresh_seconds", 90)
    candidate_rows = (
        await db.execute(
            select(m.Pilot, m.LatestLocation)
            .join(m.LatestLocation, m.LatestLocation.pilot_id == m.Pilot.id)
            .where(
                m.Pilot.city_id == body.city_id,
                m.Pilot.verified.is_(True),
                m.Pilot.available.is_(True),
                m.Pilot.state.in_(["online_available", "assigned"]),
                m.Pilot.location_consent_at.is_not(None),
                m.LatestLocation.observed_at >= now() - timedelta(seconds=freshness),
            )
            .order_by(m.LatestLocation.observed_at.desc(), m.Pilot.id)
            .limit(500)
        )
    ).all()
    pilot_ids = [pilot.id for pilot, _location in candidate_rows]
    active_counts = {}
    if pilot_ids:
        active_counts = dict(
            (
                await db.execute(
                    select(m.Assignment.pilot_id, func.count())
                    .where(
                        m.Assignment.pilot_id.in_(pilot_ids),
                        m.Assignment.status.in_(["offered", "accepted", "picked_up"]),
                    )
                    .group_by(m.Assignment.pilot_id)
                )
            ).all()
        )
    pilots = []
    for pilot, location in candidate_rows:
        remaining = max(0, pilot.max_active_tasks - int(active_counts.get(pilot.id, 0)))
        if remaining:
            pilots.append(
                {
                    "id": pilot.id,
                    "remaining_capacity": 1,
                    "active_tasks": int(active_counts.get(pilot.id, 0)),
                    "_location": location,
                }
            )
    policy_model = F["fulfillment.dispatch_policies"]
    policy = await db.scalar(
        select(policy_model)
        .where(policy_model.city_id == body.city_id, policy_model.active.is_(True))
        .order_by(policy_model.version.desc())
    )
    weights = policy.weights if policy else {"pickup_distance": "1", "workload": "5"}
    strategy = logistics.DispatchStrategy()
    tasks = [{"id": task.id, "_branch": branch} for task, _unit, _child, branch in selected_tasks]

    def candidate_score(task, pilot):
        return strategy.score(
            pilot["id"], pilot["_location"], task["_branch"], pilot["active_tasks"], weights
        ).score

    started = perf_counter()
    plan = greedy_one_to_one(tasks, pilots, candidate_score)
    runtime_ms = max(0, int((perf_counter() - started) * 1000))
    objective = sum(item["score"] for item in plan)
    fallback_reason = "postgis_route_and_zone_constraints_unavailable"
    result = {
        "city_id": str(body.city_id),
        "plan": plan,
        "provenance": "deterministic_optimization_algorithm",
        "model_status": "not_a_trained_model",
        "algorithm": "bounded_greedy_one_pilot_per_task_v1",
        "policy_version": str(policy.version) if policy else "default-v1",
        "runtime_ms": runtime_ms,
        "unassigned_task_ids": [
            str(task["id"]) for task in tasks if str(task["id"]) not in {x["task_id"] for x in plan}
        ],
        "constraint_checks": {
            "assignable_task_city_and_status": True,
            "pilot_verified_available_fresh_and_consented": True,
            "pilot_capacity": True,
            "exclusive_recommendation": True,
            "zone_vehicle_route_time_windows": "not_evaluated",
        },
        "degraded_reason": fallback_reason,
        "committed": False,
    }
    await add(
        db,
        F["intelligence.ai_optimization_decisions"],
        city_id=body.city_id,
        mode="batch_recommendation",
        policy_version=result["policy_version"],
        objective_score=Decimal(str(objective)),
        plan=plan,
        constraint_checks=result["constraint_checks"],
        runtime_ms=runtime_ms,
        fallback_reason=fallback_reason,
    )
    await ai_service.log_prediction(
        db,
        "dispatch",
        actor.subject,
        "dispatch_plan_recommendation",
        {"city_id": str(body.city_id), "task_ids": [str(x) for x in body.task_ids]},
        result,
    )
    return result


@router.post("/ai/recommendations/merchants", tags=["AI intelligence"])
async def ai_recommend_merchants(body: s.RecommendationQueryIn, actor: Actor, db: DB):
    city = await Repository(db).require(m.City, body.city_id)
    if not city.active:
        raise BusinessError("city_unavailable", "City is not active", 409)
    popularity = (
        select(
            m.MerchantOrder.branch_id.label("branch_id"),
            func.count(func.distinct(m.Order.id)).label("orders_30d"),
        )
        .join(m.Order, m.Order.id == m.MerchantOrder.order_id)
        .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
        .where(m.Branch.city_id == city.id, m.Order.created_at >= now() - timedelta(days=30))
        .group_by(m.MerchantOrder.branch_id)
        .subquery()
    )
    query = (
        select(m.Branch, func.coalesce(popularity.c.orders_30d, 0))
        .outerjoin(popularity, popularity.c.branch_id == m.Branch.id)
        .where(
            m.Branch.city_id == city.id,
            m.Branch.status == "approved",
            m.Branch.accepting_orders.is_(True),
        )
    )
    if body.category_id:
        category = await Repository(db).require(m.Category, body.category_id)
        if category.regulated:
            raise BusinessError(
                "regulated_category_unavailable",
                "Regulated categories require an approved compliance workflow",
                409,
            )
        query = query.where(
            m.Branch.id.in_(
                select(m.BranchArea.branch_id)
                .join(m.ServiceArea, m.ServiceArea.id == m.BranchArea.area_id)
                .where(
                    m.ServiceArea.zone_id.in_(
                        select(m.Zone.id).where(m.Zone.city_id == city.id, m.Zone.active.is_(True))
                    ),
                    m.BranchArea.category_id == body.category_id,
                )
            )
        )
    rows = (
        await db.execute(
            query.order_by(func.coalesce(popularity.c.orders_30d, 0).desc(), m.Branch.id).limit(
                body.limit
            )
        )
    ).all()
    result = {
        "city_id": str(city.id),
        "items": [
            {
                "branch_id": str(branch.id),
                "name": branch.name,
                "recent_orders": int(count),
                "organic": True,
            }
            for branch, count in rows
        ],
        "provenance": "deterministic_popularity_and_availability",
        "model_status": "untrained_baseline",
        "personal_history_used": False,
    }
    await ai_service.log_prediction(
        db,
        "recommendations",
        actor.subject,
        "merchant_recommendations",
        {
            "city_id": str(city.id),
            "category_id": str(body.category_id) if body.category_id else None,
        },
        result,
    )
    return result


@router.post("/ai/recommendations/products", tags=["AI intelligence"])
async def ai_recommend_products(body: s.RecommendationQueryIn, actor: Actor, db: DB):
    city = await Repository(db).require(m.City, body.city_id)
    if not city.active:
        raise BusinessError("city_unavailable", "City is not active", 409)
    if body.category_id:
        category = await Repository(db).require(m.Category, body.category_id)
        if category.regulated:
            raise BusinessError(
                "regulated_category_unavailable",
                "Regulated categories require an approved compliance workflow",
                409,
            )
    price_model = m.Price
    query = (
        select(m.Product, m.Variant, m.Branch, m.Stock, price_model)
        .join(m.Variant, m.Variant.product_id == m.Product.id)
        .join(m.Stock, m.Stock.variant_id == m.Variant.id)
        .join(m.Branch, m.Branch.id == m.Stock.branch_id)
        .join(m.Category, m.Category.id == m.Product.category_id)
        .join(price_model, price_model.variant_id == m.Variant.id)
        .where(
            m.Product.active.is_(True),
            m.Category.regulated.is_(False),
            m.Branch.city_id == city.id,
            m.Branch.status == "approved",
            m.Branch.accepting_orders.is_(True),
            m.Stock.on_hand > m.Stock.reserved,
            price_model.branch_id == m.Branch.id,
            price_model.starts_at <= now(),
            (price_model.ends_at.is_(None) | (price_model.ends_at > now())),
        )
    )
    if body.category_id:
        query = query.where(m.Product.category_id == body.category_id)
    rows = (
        await db.execute(query.order_by(m.Product.name, m.Variant.name).limit(body.limit))
    ).all()
    result = {
        "city_id": str(city.id),
        "items": [
            {
                "product_id": str(product.id),
                "product": product.name,
                "variant_id": str(variant.id),
                "variant": variant.name,
                "branch_id": str(branch.id),
                "available_quantity": str(stock.on_hand - stock.reserved),
                "price": str(price.amount),
                "currency": price.currency,
                "organic": True,
            }
            for product, variant, branch, stock, price in rows
        ],
        "provenance": "deterministic_availability_filtered_catalog",
        "model_status": "untrained_baseline",
        "personal_history_used": False,
    }
    await ai_service.log_prediction(
        db,
        "recommendations",
        actor.subject,
        "product_recommendations",
        {
            "city_id": str(city.id),
            "category_id": str(body.category_id) if body.category_id else None,
        },
        result,
    )
    return result


@router.post("/ai/eta/predict", tags=["AI intelligence"])
async def ai_eta_predict(body: s.EtaPredictIn, actor: Actor, request: Request, db: DB):
    task, unit, child, branch = await logistics.task_context(db, body.task_id)
    order = await Repository(db).require(m.Order, child.order_id)
    authorized = str(order.user_id) == actor.subject
    if not authorized:
        assignment = await db.scalar(
            select(m.Assignment).where(
                m.Assignment.task_id == task.id,
                m.Assignment.status.in_(["accepted", "picked_up"]),
            )
        )
        if assignment:
            pilot = await Repository(db).require(m.Pilot, assignment.pilot_id)
            authorized = str(pilot.user_id) == actor.subject
        if not authorized:
            await scoped(db, actor, "ai.read", branch.organization_id, branch.city_id, branch.id)
    result = await eta_engine.estimate(
        db,
        task,
        unit,
        child,
        branch,
        request.app.state.routing_provider,
        request.app.state.settings,
    )
    result["provenance"] = "deterministic_rule_with_routing_provider"
    result["model_status"] = "untrained_baseline"
    result["model_version"] = "eta-v1"
    await ai_service.log_prediction(
        db,
        "eta",
        actor.subject,
        "delivery_eta",
        {"task_id": str(task.id)},
        result,
        branch.organization_id,
    )
    return result


async def _order_risk(db, order):
    children = (
        await db.scalars(select(m.MerchantOrder).where(m.MerchantOrder.order_id == order.id))
    ).all()
    reasons = []
    score = Decimal("0.00")
    timestamp = now()
    for child in children:
        age = (timestamp - child.created_at).total_seconds()
        if child.status == "pending" and age > 600:
            score = max(score, Decimal("0.75"))
            reasons.append("merchant_acceptance_over_10m")
        if child.status == "preparing" and age > 1800:
            score = max(score, Decimal("0.65"))
            reasons.append("preparation_over_30m_without_actual_start_time")
        task = await db.scalar(
            select(m.DeliveryTask)
            .join(m.FulfillmentUnit, m.FulfillmentUnit.id == m.DeliveryTask.fulfillment_unit_id)
            .where(m.FulfillmentUnit.merchant_order_id == child.id)
        )
        if task and child.status == "ready" and task.status == "unassigned" and age > 900:
            score = max(score, Decimal("0.70"))
            reasons.append("ready_task_unassigned_over_15m")
    return {
        "subject_id": str(order.id),
        "risk_score": str(score),
        "risk_level": "review" if score >= Decimal("0.60") else "normal",
        "reason_codes": sorted(set(reasons)),
        "recommendation": (
            "Review operational state; this signal never cancels or penalizes an account."
        ),
        "provenance": "deterministic_rule",
        "model_status": "untrained_baseline",
        "model_version": "risk-v1",
        "generated_at": timestamp.isoformat(),
    }


async def _authorize_ai_order(db, actor, order):
    if str(order.user_id) == actor.subject:
        return None
    rows = (
        (
            await db.execute(
                select(m.Branch)
                .join(m.MerchantOrder, m.MerchantOrder.branch_id == m.Branch.id)
                .where(m.MerchantOrder.order_id == order.id)
            )
        )
        .scalars()
        .all()
    )
    for branch in rows:
        try:
            await scoped(db, actor, "ai.read", branch.organization_id, branch.city_id, branch.id)
            return branch.organization_id
        except BusinessError:
            continue
    raise BusinessError("forbidden", "Access denied for this order risk signal", 403)


@router.get("/ai/risk/orders/{order_id}", tags=["AI intelligence"])
async def ai_order_risk(order_id: UUID, actor: Actor, db: DB):
    order = await Repository(db).require(m.Order, order_id)
    organization_id = await _authorize_ai_order(db, actor, order)
    result = await _order_risk(db, order)
    run_id = await ai_service.log_prediction(
        db,
        "risk",
        actor.subject,
        "order_operational_risk",
        {"order_id": str(order.id)},
        result,
        organization_id,
    )
    await add(
        db,
        F["intelligence.ai_risk_signals"],
        run_id=run_id,
        subject_digest=hashlib.sha256(("order:" + str(order.id)).encode()).hexdigest(),
        kind="operational_delay",
        score=Decimal(result["risk_score"]),
        review_status="needs_review" if result["risk_level"] == "review" else "monitor",
    )
    return result


@router.get("/ai/risk/deliveries/{delivery_id}", tags=["AI intelligence"])
async def ai_delivery_risk(delivery_id: UUID, actor: Actor, db: DB):
    task, _unit, child, branch = await logistics.task_context(db, delivery_id)
    order = await Repository(db).require(m.Order, child.order_id)
    assignment = await db.scalar(
        select(m.Assignment).where(
            m.Assignment.task_id == task.id,
            m.Assignment.status.in_(["accepted", "picked_up"]),
        )
    )
    if str(order.user_id) == actor.subject:
        organization_id = None
    elif assignment:
        pilot = await Repository(db).require(m.Pilot, assignment.pilot_id)
        if str(pilot.user_id) == actor.subject:
            organization_id = branch.organization_id
        else:
            organization_id = await _authorize_ai_order(db, actor, order)
    else:
        organization_id = await _authorize_ai_order(db, actor, order)
    result = await _order_risk(db, order)
    result["delivery_id"] = str(task.id)
    run_id = await ai_service.log_prediction(
        db,
        "risk",
        actor.subject,
        "delivery_operational_risk",
        {"delivery_id": str(task.id)},
        result,
        organization_id or branch.organization_id,
    )
    await add(
        db,
        F["intelligence.ai_risk_signals"],
        run_id=run_id,
        subject_digest=hashlib.sha256(("delivery:" + str(task.id)).encode()).hexdigest(),
        kind="operational_delay",
        score=Decimal(result["risk_score"]),
        review_status="needs_review" if result["risk_level"] == "review" else "monitor",
    )
    return result


@router.get("/ai/models", tags=["AI model lifecycle"])
async def ai_models(actor: Actor, db: DB):
    registry = F["intelligence.ai_model_registry"]
    versions = F["intelligence.ai_model_versions"]
    rows = (
        await db.execute(
            select(registry, versions)
            .join(versions, versions.model_id == registry.id)
            .order_by(registry.name, versions.created_at.desc())
        )
    ).all()
    return {
        "items": [
            {
                "model_id": str(model.id),
                "name": model.name,
                "purpose": model.purpose,
                "provider": model.provider,
                "version_id": str(version.id),
                "version": version.version,
                "algorithm": version.algorithm,
                "status": version.status,
                "validation_passed": version.validation_passed,
                "metrics": version.metrics,
            }
            for model, version in rows
        ]
    }


@router.get("/ai/models/{model_id}/metrics", tags=["AI model lifecycle"])
async def ai_model_metrics(model_id: UUID, actor: Actor, db: DB):
    registry = F["intelligence.ai_model_registry"]
    versions = F["intelligence.ai_model_versions"]
    rows = (
        await db.execute(
            select(
                versions.version,
                versions.algorithm,
                versions.status,
                versions.metrics,
                versions.validation_passed,
            )
            .where(versions.model_id == model_id)
            .order_by(versions.created_at.desc())
        )
    ).all()
    if not await db.scalar(select(registry.id).where(registry.id == model_id)):
        raise BusinessError("model_not_found", "Model was not found", 404)
    return {"model_id": str(model_id), "versions": [dict(row._mapping) for row in rows]}


@router.post("/ai/models/{model_id}/evaluate", tags=["AI model lifecycle"])
async def ai_evaluate_model(model_id: UUID, body: s.AiEvaluateIn, actor: Actor, db: DB):
    await scoped(db, actor, "ai.manage")
    registry = F["intelligence.ai_model_registry"]
    versions = F["intelligence.ai_model_versions"]
    model = await db.scalar(select(registry).where(registry.id == model_id))
    if not model:
        raise BusinessError("model_not_found", "Model was not found", 404)
    if model.name != "quickbuddy-demand-baseline":
        raise BusinessError("evaluation_not_supported", "This baseline has no evaluator", 422)
    city = await Repository(db).require(m.City, body.city_id)
    version = await db.scalar(
        select(versions).where(versions.model_id == model_id).order_by(versions.created_at.desc())
    )
    result = await ai_service.demand_backtest(db, city)
    evaluation = await add(
        db,
        F["intelligence.ai_evaluation_runs"],
        version_id=version.id,
        dataset_reference=f"city:{city.id}:point-in-time-orders-28d",
        metrics=result,
        status="completed" if result["sample_count"] else "insufficient_data",
    )
    return {"evaluation_id": evaluation.id, **result, "model_status": "untrained_baseline"}


@router.get("/ai/copilot/status", tags=["AI copilot"])
async def ai_copilot_status(actor: Actor, request: Request):
    gateway = request.app.state.ai_gateway
    return {
        "status": "configured" if gateway.available else "deterministic_fallback",
        "provider_configured": gateway.available,
        "provider": request.app.state.settings.ai_provider,
        "model": request.app.state.settings.ai_model or None,
        "agents": [
            {"id": spec.key, "purpose": spec.purpose, "read_only_tools": list(spec.tools)}
            for spec in AI_AGENTS.values()
        ],
        "provenance": "shared_gateway_role_scoped_read_only_context",
    }


@router.post(
    "/ai/agents/{agent}/query",
    response_model=s.AiAgentQueryOut,
    tags=["AI agents"],
)
async def ai_agent_query(
    agent: str, body: s.AiAgentQueryIn, actor: Actor, request: Request, db: DB
):
    await actor_budget(request, actor, "ai-agent-query", 20)
    spec = AI_AGENTS.get(agent)
    if spec is None:
        raise BusinessError("agent_not_found", "AI assistant is not available", 404)
    # Redis is the shared limiter. If it is unavailable, never send this request to an external
    # provider; still return the scoped deterministic evidence summary.
    allow_provider = request.app.state.ai_gateway.available
    try:
        bucket = int(now().timestamp()) // 60
        key = f"quickbuddy:ai:rate:{actor.subject}:{bucket}"
        count = await request.app.state.redis.incr(key)
        if count == 1:
            await request.app.state.redis.expire(key, 120)
        if count > 20:
            raise BusinessError("rate_limited", "AI request rate limit exceeded", 429)
    except BusinessError:
        raise
    except Exception:
        allow_provider = False
    evidence = await ai_agents.context_for(db, actor, agent, body)
    result = await request.app.state.ai_gateway.answer(
        spec, body.question, evidence, allow_provider
    )
    question_digest = hashlib.sha256(body.question.encode()).hexdigest()
    baseline_key = {
        "customer": "recommendations",
        "merchant": "recommendations",
        "pilot": "dispatch",
        "city": "demand",
        "admin": "risk",
        "support": "risk",
    }[agent]
    await ai_service.log_prediction(
        db,
        baseline_key,
        actor.subject,
        f"{agent}_assistant_query",
        {"question_digest": question_digest, "agent": agent},
        {
            "provider": result.provider,
            "model": result.model,
            "fallback": result.fallback,
            "latency_ms": result.latency_ms,
        },
    )
    return {
        "agent": agent,
        "answer": result.answer,
        "evidence": evidence,
        "provider": result.provider,
        "model": result.model,
        "fallback": result.fallback,
        "latency_ms": result.latency_ms,
    }


@router.post("/ai/copilot/query", tags=["AI copilot"])
async def ai_copilot_query(body: s.CopilotQueryIn, actor: Actor):
    raise BusinessError("copilot_unavailable", "No approved LLM provider is configured", 503)


@router.post(
    "/fulfillment/recurring-plans",
    status_code=201,
    tags=["Recurring commerce"],
)
async def create_recurring_plan(body: s.RecurringPlanCreateIn, actor: Actor, db: DB):
    plan = await recurring.create_plan(db, actor, body)
    return await recurring.plan_view(db, plan)


@router.get("/fulfillment/recurring-plans", tags=["Recurring commerce"])
async def list_recurring_plans(actor: Actor, db: DB):
    Plan = F["fulfillment.recurring_order_plans"]
    plans = (
        await db.scalars(
            select(Plan)
            .where(Plan.user_id == UUID(actor.subject))
            .order_by(Plan.created_at.desc())
            .limit(50)
        )
    ).all()
    return {"items": [await recurring.plan_view(db, plan) for plan in plans]}


@router.put("/fulfillment/recurring-plans/{plan_id}/status", tags=["Recurring commerce"])
async def update_recurring_plan_status(
    plan_id: UUID, body: s.RecurringPlanStatusIn, actor: Actor, db: DB
):
    plan = await recurring.set_status(db, actor, plan_id, body.status)
    return await recurring.plan_view(db, plan)


@router.post("/fulfillment/recurring-plans/{plan_id}/skip", tags=["Recurring commerce"])
async def skip_recurring_date(plan_id: UUID, body: s.RecurringPlanSkipIn, actor: Actor, db: DB):
    return await recurring.skip_local_date(db, actor, plan_id, body.local_date)


@router.get("/fulfillment/recurring-plans/{plan_id}/occurrences", tags=["Recurring commerce"])
async def list_recurring_occurrences(plan_id: UUID, actor: Actor, db: DB):
    await recurring.owned_plan(db, actor, plan_id)
    Occurrence = F["fulfillment.scheduled_order_occurrences"]
    rows = (
        await db.scalars(
            select(Occurrence)
            .where(Occurrence.plan_id == plan_id)
            .order_by(Occurrence.scheduled_at)
            .limit(100)
        )
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "scheduled_at": row.scheduled_at,
                "status": row.status,
                "revalidation_reason": row.revalidation_reason,
                "order_id": row.order_id,
            }
            for row in rows
        ]
    }


@router.put("/operations/cities/{city_id}/dispatch-policy", tags=["Dispatch operations"])
async def set_dispatch_policy(city_id: UUID, body: s.DispatchPolicyIn, actor: Actor, db: DB):
    await scoped(db, actor, "dispatch.write", city_id=city_id)
    policy_model = F["fulfillment.dispatch_policies"]
    existing = await db.scalar(
        select(policy_model)
        .where(policy_model.city_id == city_id, policy_model.active.is_(True))
        .with_for_update()
    )
    version = 1
    if existing:
        version = existing.version + 1
        existing.active = False
    policy = await add(
        db,
        policy_model,
        city_id=city_id,
        version=version,
        weights={key: str(value) for key, value in body.weights.items()},
        active=True,
    )
    return {"id": policy.id, "city_id": city_id, "version": version, "weights": policy.weights}


@router.post("/operations/dispatch/{task_id}/reassign", tags=["Dispatch operations"])
async def reassign_delivery(
    task_id: UUID, body: s.ReassignmentIn, actor: Actor, request: Request, db: DB
):
    task, unit, child, branch = await logistics.task_context(db, task_id, True)
    await scoped(db, actor, "dispatch.write", branch.organization_id, branch.city_id, branch.id)
    if task.status == "picked_up":
        raise BusinessError(
            "custody_recovery_required",
            "Picked-up deliveries require a custody recovery workflow",
            409,
        )
    if task.status in {"delivered", "cancelled"}:
        raise BusinessError(
            "invalid_reassignment", "Completed or cancelled tasks cannot be reassigned", 409
        )
    active = await db.scalar(
        select(m.Assignment)
        .where(
            m.Assignment.task_id == task.id,
            m.Assignment.status.in_(["offered", "accepted"]),
        )
        .with_for_update()
    )
    if active:
        active.status = "reassigned"
        old_pilot = await db.get(m.Pilot, active.pilot_id)
        if old_pilot:
            old_pilot.state, old_pilot.available = "online_available", True
    task.status, task.version = "unassigned", task.version + 1
    await add(
        db,
        F["fulfillment.dispatch_events"],
        task_id=task.id,
        event_type="manual_reassignment",
        actor_id=UUID(actor.subject),
        strategy="supervisor_reason:" + body.reason,
    )
    return await logistics.offer(db, actor, task.id, body.pilot_id, request.state.request_id)


@router.post("/delivery-tasks/{task_id}/pickup", response_model=s.VersionOut, tags=["Fulfillment"])
async def pickup(task_id: UUID, body: s.VersionIn, actor: Actor, request: Request, db: DB):
    return await logistics.progress(
        db, actor, task_id, "picked_up", body.expected_version, request.state.request_id
    )


@router.post("/delivery-tasks/{task_id}/fail", response_model=s.VersionOut, tags=["Fulfillment"])
async def fail(task_id: UUID, body: s.VersionIn, actor: Actor, request: Request, db: DB):
    return await logistics.progress(
        db, actor, task_id, "failed", body.expected_version, request.state.request_id
    )


@router.post(
    "/delivery-tasks/{task_id}/acknowledge", response_model=s.VersionOut, tags=["Fulfillment"]
)
async def acknowledge(task_id: UUID, body: s.VersionIn, actor: Actor, request: Request, db: DB):
    return await logistics.recipient_complete(
        db, actor, task_id, body.expected_version, request.state.request_id
    )


@router.get("/payments/configuration", tags=["Payments"])
async def payment_configuration(actor: Actor, request: Request):
    settings = request.app.state.settings
    enabled = settings.razorpay_enabled and settings.razorpay_mode in {"test", "live"}
    return {
        "provider": "razorpay",
        "online_payment_available": enabled,
        "sandbox_payment_available": (
            settings.sandbox_payments_enabled
            and settings.app_env != "production"
            and len(settings.sandbox_webhook_secret.get_secret_value()) >= 32
        ),
        "mode": settings.razorpay_mode if enabled else "disabled",
        "key_id": settings.razorpay_key_id.get_secret_value() if enabled else None,
        "message": None if enabled else "Online payment is currently unavailable.",
    }


@router.post("/payments/intents", tags=["Payments"])
async def create_payment_intent(
    body: s.PaymentIn,
    actor: Actor,
    request: Request,
    idempotency_key: Key,
):
    factory = getattr(request.app.state, "razorpay_gateway_factory", RazorpayGateway)
    gateway = factory(request.app.state.settings)
    return await razorpay_payments.create_order(
        request.app.state.sessions,
        actor,
        body.order_id,
        idempotency_key,
        request.state.request_id,
        gateway,
    )


@router.post("/payments/razorpay/orders", tags=["Payments"], include_in_schema=False)
async def create_razorpay_order_alias(
    body: s.PaymentIn, actor: Actor, request: Request, idempotency_key: Key
):
    return await create_payment_intent(body, actor, request, idempotency_key)


@router.post("/payments/razorpay/verify", tags=["Payments"])
async def verify_razorpay_payment(body: s.RazorpayVerifyIn, actor: Actor, request: Request):
    factory = getattr(request.app.state, "razorpay_gateway_factory", RazorpayGateway)
    gateway = factory(request.app.state.settings)
    return await razorpay_payments.verify_checkout(
        request.app.state.sessions,
        actor,
        body.order_id,
        body.payment_id,
        body.signature,
        request.state.request_id,
        gateway,
    )


@router.post("/payments/razorpay/webhook", tags=["Payments"])
async def razorpay_webhook(
    request: Request,
    event_id: Annotated[str, Header(alias="X-Razorpay-Event-Id", min_length=1, max_length=128)],
    signature: Annotated[str, Header(alias="X-Razorpay-Signature", min_length=64, max_length=64)],
):
    factory = getattr(request.app.state, "razorpay_gateway_factory", RazorpayGateway)
    gateway = factory(request.app.state.settings)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 1_048_576:
                raise BusinessError("payload_too_large", "Webhook payload exceeds limit", 413)
        except ValueError as exc:
            raise BusinessError("invalid_content_length", "Invalid content length", 400) from exc
    chunks = bytearray()
    async for chunk in request.stream():
        chunks.extend(chunk)
        if len(chunks) > 1_048_576:
            raise BusinessError("payload_too_large", "Webhook payload exceeds limit", 413)
    payload = bytes(chunks)
    return await razorpay_payments.receive_webhook(
        request.app.state.sessions,
        payload,
        event_id,
        signature,
        request.state.request_id,
        gateway,
    )


@router.get("/payments/{payment_id}", response_model=s.PaymentOut, tags=["Payments"])
async def get_payment(payment_id: UUID, actor: Actor, db: DB):
    payment = await Repository(db).require(m.PaymentIntent, payment_id)
    order = await Repository(db).require(m.Order, payment.order_id)
    owned(actor, order.user_id)
    return payment


@router.post("/finance/currencies", response_model=s.IdOut, status_code=201, tags=["Finance"])
async def currency(body: s.CurrencyIn, actor: Actor, db: DB):
    await scoped(db, actor, "finance.configure")
    return await add(db, m.Currency, **body.model_dump())


@router.post("/finance/accounts", response_model=s.IdOut, status_code=201, tags=["Finance"])
async def account(body: s.AccountIn, actor: Actor, db: DB):
    await scoped(db, actor, "finance.write", body.organization_id)
    book = await Repository(db).require(m.LedgerBook, body.book_id)
    if book.organization_id != body.organization_id or book.currency != body.currency:
        raise BusinessError(
            "ledger_book_scope", "Account must match its legal entity/currency book", 403
        )
    return await add(db, m.LedgerAccount, **body.model_dump())


@router.post(
    "/organizations/{organization_id}/legal-entities",
    response_model=s.IdOut,
    status_code=201,
    tags=["Merchants"],
)
async def legal_entity(organization_id: UUID, body: s.LegalEntityIn, actor: Actor, db: DB):
    await scoped(db, actor, "merchant.write", organization_id)
    return await add(
        db,
        F["merchant.merchant_legal_entities"],
        organization_id=organization_id,
        **body.model_dump(),
    )


@router.post("/finance/books", response_model=s.IdOut, status_code=201, tags=["Finance"])
async def ledger_book(body: s.BookIn, actor: Actor, db: DB):
    await scoped(db, actor, "finance.write", body.organization_id)
    entity = await Repository(db).require(
        F["merchant.merchant_legal_entities"], body.legal_entity_id
    )
    if entity.organization_id != body.organization_id:
        raise BusinessError(
            "legal_entity_scope", "Legal entity belongs to another organization", 403
        )
    return await add(db, m.LedgerBook, **body.model_dump())


@router.post("/finance/journals", response_model=s.StateOut, status_code=201, tags=["Finance"])
async def journal(body: s.JournalIn, actor: Actor, db: DB):
    await scoped(db, actor, "finance.write", body.organization_id)
    return await finance.post_journal(
        db,
        body.organization_id,
        body.idempotency_key,
        body.description,
        [(line.account_id, line.amount) for line in body.lines],
    )


@router.post(
    "/finance/journals/{journal_id}/reversal",
    response_model=s.StateOut,
    status_code=201,
    tags=["Finance"],
)
async def reversal(journal_id: UUID, actor: Actor, db: DB, idempotency_key: Key):
    return await finance.reverse_journal(db, actor, journal_id, idempotency_key)


@router.post(
    "/finance/sandbox/payment-intents",
    response_model=s.PaymentOut,
    status_code=201,
    tags=["Sandbox finance"],
)
async def payment(body: s.PaymentIn, actor: Actor, request: Request, db: DB):
    return await finance.payment_intent(
        db, actor, body.order_id, finance.SandboxGateway(request.app.state.settings)
    )


@router.get("/finance/payments/{payment_id}", response_model=s.PaymentOut, tags=["Finance"])
async def payment_status(payment_id: UUID, actor: Actor, db: DB):
    payment = await Repository(db).require(m.PaymentIntent, payment_id)
    order = await Repository(db).require(m.Order, payment.order_id)
    owned(actor, order.user_id)
    return payment


@router.post(
    "/finance/sandbox/payments/{payment_id}/complete",
    response_model=s.PaymentOut,
    tags=["Sandbox finance"],
)
async def complete_sandbox_payment(payment_id: UUID, actor: Actor, request: Request, db: DB):
    """Complete an owned sandbox intent in development/test through the signed webhook path."""
    if request.app.state.settings.app_env == "production":
        raise BusinessError(
            "sandbox_disabled", "Sandbox completion is unavailable in production", 503
        )
    gateway = finance.SandboxGateway(request.app.state.settings)
    payment = await Repository(db).require(m.PaymentIntent, payment_id)
    order = await Repository(db).require(m.Order, payment.order_id)
    owned(actor, order.user_id)
    payload = json.dumps(
        {
            "event_id": f"SANDBOX:customer-completion:{payment.id}",
            "payment_id": str(payment.id),
            "status": "confirmed",
            "currency": payment.currency,
            "amount": str(payment.amount),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(gateway.secret.encode(), payload, "sha256").hexdigest()
    return await finance.webhook(db, gateway, payload, signature, request.state.request_id)


@router.post("/finance/sandbox/webhook", response_model=s.PaymentOut, tags=["Sandbox finance"])
async def sandbox_webhook(
    request: Request,
    db: DB,
    signature: Annotated[str, Header(alias="X-Sandbox-Signature", min_length=64, max_length=64)],
):
    gateway = finance.SandboxGateway(request.app.state.settings)
    payload = await request.body()
    if len(payload) > 8192:
        raise BusinessError("payload_too_large", "Webhook payload exceeds limit", 413)
    return await finance.webhook(db, gateway, payload, signature, request.state.request_id)


@router.post(
    "/finance/sandbox/payments/{payment_id}/refunds",
    response_model=s.StateOut,
    status_code=201,
    tags=["Sandbox finance"],
)
async def refund(payment_id: UUID, body: s.RefundIn, actor: Actor, request: Request, db: DB):
    return await finance.refund(
        db,
        actor,
        payment_id,
        body.amount,
        body.idempotency_key,
        finance.SandboxGateway(request.app.state.settings),
        body.organization_id,
        request.state.request_id,
        body.approval_id,
    )


async def _support_scope(db, actor):
    user = await db.get(m.User, UUID(actor.subject))
    if not user or user.status != "active":
        raise BusinessError("forbidden", "Access denied", 403)
    rows = (
        await db.execute(
            select(m.RoleAssignment, m.Role.name)
            .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
            .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
            .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
            .where(m.RoleAssignment.user_id == user.id, m.Permission.code == "support.write")
        )
    ).all()
    global_support = any(
        role in {"support_agent", "platform_super_admin"}
        and assignment.organization_id is None
        and assignment.city_id is None
        and assignment.branch_id is None
        for assignment, role in rows
    )
    organization_ids = {
        assignment.organization_id
        for assignment, _role in rows
        if assignment.organization_id is not None
        and assignment.city_id is None
        and assignment.branch_id is None
        and await db.scalar(
            select(m.Membership.id).where(
                m.Membership.user_id == user.id,
                m.Membership.organization_id == assignment.organization_id,
                m.Membership.status == "active",
            )
        )
    }
    return global_support, organization_ids


async def _support_ticket_access(db, actor, ticket):
    global_support, organization_ids = await _support_scope(db, actor)
    if global_support or ticket.organization_id in organization_ids:
        return
    raise BusinessError("forbidden", "Ticket is outside your support assignment scope", 403)


@router.get("/support/tickets", tags=["Operations"])
async def support_queue(
    actor: Actor, request: Request, db: DB, cursor: str | None = None, limit: Limit = 50
):
    global_support, organization_ids = await _support_scope(db, actor)
    if not global_support and not organization_ids:
        raise BusinessError("forbidden", "An active support assignment is required", 403)
    predicates = [
        or_(m.Ticket.assigned_to_id.is_(None), m.Ticket.assigned_to_id == UUID(actor.subject))
    ]
    if not global_support:
        predicates.append(m.Ticket.organization_id.in_(organization_ids))
    tickets, next_id = await Repository(db).page(
        m.Ticket, predicates, after=decode_cursor(cursor), limit=limit
    )
    for row in tickets:
        await audit(
            db, actor, "support.ticket.read", row.id, request.state.request_id, row.organization_id
        )
    return {
        "items": [
            {
                "id": row.id,
                "subject": row.subject,
                "status": row.status,
                "order_id": row.order_id,
                "created_at": row.created_at,
                "assigned_to_me": row.assigned_to_id == UUID(actor.subject),
            }
            for row in tickets
        ],
        "next_cursor": base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=")
        if next_id
        else None,
    }


@router.post("/support/tickets/{ticket_id}/claim", tags=["Operations"])
async def claim_support_ticket(ticket_id: UUID, actor: Actor, request: Request, db: DB):
    ticket = await Repository(db).require(m.Ticket, ticket_id, lock=True)
    await _support_ticket_access(db, actor, ticket)
    if ticket.assigned_to_id is not None and ticket.assigned_to_id != UUID(actor.subject):
        raise BusinessError("ticket_claimed", "Ticket is already assigned to another agent", 409)
    if ticket.status == "resolved":
        raise BusinessError("ticket_resolved", "Resolved tickets cannot be claimed", 409)
    if ticket.assigned_to_id is None:
        previous = ticket.status
        ticket.assigned_to_id = UUID(actor.subject)
        ticket.status = "assigned"
        await audit(
            db,
            actor,
            "support.ticket_claim",
            ticket.id,
            request.state.request_id,
            ticket.organization_id,
            previous=previous,
            current="assigned",
        )
    return {"id": ticket.id, "status": ticket.status, "assigned_to_me": True}


@router.get("/support/tickets/{ticket_id}/messages", tags=["Operations"])
async def support_ticket_messages(ticket_id: UUID, actor: Actor, request: Request, db: DB):
    ticket = await Repository(db).require(m.Ticket, ticket_id)
    await _support_ticket_access(db, actor, ticket)
    if ticket.assigned_to_id != UUID(actor.subject):
        raise BusinessError(
            "ticket_not_claimed", "Claim this ticket before reading its conversation", 403
        )
    await audit(
        db,
        actor,
        "support.ticket_conversation.read",
        ticket.id,
        request.state.request_id,
        ticket.organization_id,
    )
    messages = (
        await db.scalars(
            select(m.TicketMessage)
            .where(m.TicketMessage.ticket_id == ticket.id)
            .order_by(m.TicketMessage.created_at, m.TicketMessage.id)
        )
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "body": row.body,
                "author": "agent" if row.author_id == UUID(actor.subject) else "customer",
                "created_at": row.created_at,
            }
            for row in messages
        ]
    }


@router.post("/support/tickets/{ticket_id}/resolve", tags=["Operations"])
async def resolve_support_ticket(ticket_id: UUID, actor: Actor, request: Request, db: DB):
    ticket = await Repository(db).require(m.Ticket, ticket_id, lock=True)
    await _support_ticket_access(db, actor, ticket)
    if ticket.assigned_to_id != UUID(actor.subject):
        raise BusinessError(
            "ticket_not_assigned", "Only the assigned agent can resolve this ticket", 403
        )
    if ticket.status == "resolved":
        return {"id": ticket.id, "status": ticket.status}
    ticket.status = "resolved"
    await audit(
        db,
        actor,
        "support.ticket_resolve",
        ticket.id,
        request.state.request_id,
        ticket.organization_id,
        previous="assigned",
        current="resolved",
    )
    return {"id": ticket.id, "status": ticket.status}


@router.post("/support/tickets", response_model=s.StateOut, status_code=201, tags=["Operations"])
async def ticket(body: s.TicketIn, actor: Actor, db: DB):
    if body.order_id:
        order = await Repository(db).require(m.Order, body.order_id)
        owned(actor, order.user_id)
    return await add(db, m.Ticket, user_id=UUID(actor.subject), **body.model_dump())


@router.get(
    "/me/support/tickets",
    response_model=s.Page[s.CustomerTicketOut],
    tags=["Customer support"],
)
async def my_support_tickets(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    """Return only the authenticated customer's own support cases."""
    return await page(
        db,
        m.Ticket,
        [m.Ticket.user_id == UUID(actor.subject)],
        s.CustomerTicketOut,
        cursor,
        limit,
    )


@router.get(
    "/me/support/tickets/{ticket_id}/messages",
    response_model=s.Page[s.CustomerTicketMessageOut],
    tags=["Customer support"],
)
async def my_support_ticket_messages(
    ticket_id: UUID,
    actor: Actor,
    db: DB,
    cursor: str | None = None,
    limit: Limit = 50,
):
    """Read a customer's own conversation without exposing support-agent identities."""
    ticket = await db.scalar(
        select(m.Ticket).where(m.Ticket.id == ticket_id, m.Ticket.user_id == UUID(actor.subject))
    )
    if ticket is None:
        raise BusinessError("not_found", "Support ticket not found", 404)
    after = None
    if cursor:
        try:
            raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
            timestamp, identifier = raw.rsplit("|", 1)
            after = (datetime.fromisoformat(timestamp), UUID(identifier))
            if after[0].tzinfo is None:
                raise ValueError("timestamp must include timezone")
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            raise BusinessError("invalid_cursor", "Invalid page cursor", 422) from exc
    statement = select(m.TicketMessage).where(m.TicketMessage.ticket_id == ticket.id)
    if after:
        statement = statement.where(
            tuple_(m.TicketMessage.created_at, m.TicketMessage.id) > tuple_(*after)
        )
    all_rows = list(
        (
            await db.scalars(
                statement.order_by(m.TicketMessage.created_at, m.TicketMessage.id).limit(limit + 1)
            )
        ).all()
    )
    rows = all_rows[:limit]
    next_cursor = None
    if len(all_rows) > limit and rows:
        last = rows[-1]
        payload = f"{last.created_at.isoformat()}|{last.id}"
        next_cursor = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return {
        "items": [
            {
                "id": row.id,
                "author": "you" if row.author_id == UUID(actor.subject) else "support",
                "body": row.body,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "next_cursor": next_cursor,
    }


@router.post(
    "/support/tickets/{ticket_id}/messages",
    response_model=s.MessageOut,
    status_code=201,
    tags=["Operations"],
)
async def message(ticket_id: UUID, body: s.MessageIn, actor: Actor, request: Request, db: DB):
    ticket = await Repository(db).require(m.Ticket, ticket_id)
    agent_reply = str(ticket.user_id) != actor.subject
    if agent_reply:
        await _support_ticket_access(db, actor, ticket)
        if ticket.assigned_to_id != UUID(actor.subject):
            raise BusinessError("ticket_not_assigned", "Claim this ticket before replying", 403)
    if ticket.status == "resolved":
        raise BusinessError("ticket_resolved", "Resolved tickets cannot receive messages", 409)
    created = await add(
        db, m.TicketMessage, ticket_id=ticket.id, author_id=UUID(actor.subject), body=body.body
    )
    if agent_reply:
        await audit(
            db,
            actor,
            "support.ticket_reply",
            ticket.id,
            request.state.request_id,
            ticket.organization_id,
        )
    return created


@router.get("/audit/events", response_model=s.Page[s.AuditOut], tags=["Operations"])
async def audit_events(
    organization_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    await scoped(db, actor, "audit.read", organization_id)
    return await page(
        db,
        m.AuditEvent,
        [m.AuditEvent.organization_id == organization_id],
        s.AuditOut,
        cursor,
        limit,
    )


@router.post(
    "/finance/refund-approvals", response_model=s.StateOut, status_code=201, tags=["Finance"]
)
async def request_refund_approval(body: s.RefundApprovalIn, actor: Actor, db: DB):
    await scoped(db, actor, "merchant.write", body.organization_id)
    child = await db.scalar(
        select(m.MerchantOrder.id)
        .join(m.Branch)
        .where(
            m.MerchantOrder.order_id == body.order_id,
            m.Branch.organization_id == body.organization_id,
        )
    )
    if not child:
        raise BusinessError("forbidden", "No merchant order in the requested organization", 403)
    return await add(
        db,
        F["operations.refund_approval_requests"],
        requested_by=UUID(actor.subject),
        status="pending",
        **body.model_dump(),
    )


@router.get("/finance/authorized-organizations", tags=["Finance"])
async def finance_organizations(actor: Actor, db: DB):
    """List only organizations for which the current user has finance.read."""
    user = await db.get(m.User, UUID(actor.subject))
    if not user or user.status != "active":
        raise BusinessError("forbidden", "Access denied", 403)
    assignments = (
        await db.execute(
            select(m.RoleAssignment, m.Role.name)
            .join(m.Role)
            .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
            .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
            .where(
                m.RoleAssignment.user_id == user.id,
                m.Permission.code == "finance.read",
            )
        )
    ).all()
    is_platform_admin = any(
        role == "platform_super_admin" and row.organization_id is None for row, role in assignments
    )
    if is_platform_admin:
        rows = (await db.scalars(select(m.Organization).order_by(m.Organization.name))).all()
    else:
        organization_ids = {
            row.organization_id
            for row, _ in assignments
            if row.organization_id and row.city_id is None and row.branch_id is None
        }
        if organization_ids:
            memberships = set(
                (
                    await db.scalars(
                        select(m.Membership.organization_id).where(
                            m.Membership.user_id == user.id,
                            m.Membership.status == "active",
                            m.Membership.organization_id.in_(organization_ids),
                        )
                    )
                ).all()
            )
            organization_ids &= memberships
        rows = (
            (
                await db.scalars(
                    select(m.Organization)
                    .where(m.Organization.id.in_(organization_ids))
                    .order_by(m.Organization.name)
                )
            ).all()
            if organization_ids
            else []
        )
    return {"items": [{"id": row.id, "name": row.name} for row in rows]}


@router.get("/finance/refund-approvals", tags=["Finance"])
async def refund_approval_queue(
    organization_id: UUID,
    actor: Actor,
    request: Request,
    db: DB,
    cursor: str | None = None,
    limit: Limit = 50,
):
    await scoped(db, actor, "finance.read", organization_id)
    Approval = F["operations.refund_approval_requests"]
    rows, next_id = await Repository(db).page(
        Approval,
        [Approval.organization_id == organization_id],
        after=decode_cursor(cursor),
        limit=limit,
    )
    for row in rows:
        await audit(
            db, actor, "refund_approval.read", row.id, request.state.request_id, organization_id
        )
    return {
        "items": [
            {
                "id": row.id,
                "order_id": row.order_id,
                "requested_by": row.requested_by,
                "organization_id": row.organization_id,
                "amount": str(row.amount),
                "status": row.status,
                "created_at": row.created_at,
            }
            for row in rows
        ],
        "next_cursor": (
            base64.urlsafe_b64encode(next_id.bytes).decode().rstrip("=") if next_id else None
        ),
    }


@router.post(
    "/finance/refund-approvals/{approval_id}/decision", response_model=s.StateOut, tags=["Finance"]
)
async def decide_refund(
    approval_id: UUID, body: s.ApprovalDecisionIn, actor: Actor, request: Request, db: DB
):
    approval = await Repository(db).require(
        F["operations.refund_approval_requests"], approval_id, lock=True
    )
    await scoped(db, actor, "finance.write", approval.organization_id)
    if str(approval.requested_by) == actor.subject:
        raise BusinessError(
            "separation_of_duties", "Requester cannot approve their own refund", 403
        )
    if approval.status != "pending":
        raise BusinessError("already_decided", "Approval was already decided")
    await add(
        db,
        F["operations.refund_approval_decisions"],
        request_id=approval.id,
        decided_by=UUID(actor.subject),
        decision=body.decision,
        reason=body.reason,
    )
    approval.status = body.decision
    await audit(
        db,
        actor,
        "refund.approval",
        approval.id,
        request.state.request_id,
        approval.organization_id,
        decision=body.decision,
    )
    return approval


@router.patch("/carts/{cart_id}/items/{item_id}", response_model=s.CartItemOut, tags=["Commerce"])
async def quantity(cart_id: UUID, item_id: UUID, body: s.QuantityIn, actor: Actor, db: DB):
    cart = await commerce.cart_context(db, actor, cart_id)
    if cart.version != body.expected_version:
        raise BusinessError("version_conflict", "Cart version changed")
    item = await Repository(db).require(m.CartItem, item_id)
    if item.cart_id != cart.id:
        raise BusinessError("not_found", "Cart item not found", 404)
    item.quantity = body.quantity
    cart.version += 1
    return item


@router.get("/orders/{order_id}/history", response_model=s.Page[s.HistoryOut], tags=["Commerce"])
async def order_history(
    order_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    order = await Repository(db).require(m.Order, order_id)
    owned(actor, order.user_id)
    return await page(
        db, m.OrderHistory, [m.OrderHistory.order_id == order.id], s.HistoryOut, cursor, limit
    )


@router.get(
    "/orders/{order_id}/delivery-tasks", response_model=s.Page[s.TaskOut], tags=["Fulfillment"]
)
async def order_tasks(
    order_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    order = await Repository(db).require(m.Order, order_id)
    owned(actor, order.user_id)
    units = (
        select(m.FulfillmentUnit.id)
        .join(m.MerchantOrder)
        .where(m.MerchantOrder.order_id == order.id)
    )
    return await page(
        db,
        m.DeliveryTask,
        [m.DeliveryTask.fulfillment_unit_id.in_(units)],
        s.TaskOut,
        cursor,
        limit,
    )


@router.get(
    "/inventory/branches/{branch_id}/movements",
    response_model=s.Page[s.MovementOut],
    tags=["Inventory"],
)
async def stock_movements(
    branch_id: UUID, actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50
):
    await branch_scope(db, actor, branch_id, "inventory.read")
    stocks = select(m.Stock.id).where(m.Stock.branch_id == branch_id)
    return await page(
        db, m.StockMovement, [m.StockMovement.stock_id.in_(stocks)], s.MovementOut, cursor, limit
    )


@router.post("/geo/serviceability", response_model=s.ServiceabilityOut, tags=["Geography"])
async def serviceability(body: s.ServiceabilityIn, actor: Actor, db: DB):
    branch = await Repository(db).require(m.Branch, body.branch_id)
    window = await Repository(db).require(m.Window, body.window_id)
    address = await Repository(db).require(m.Address, body.address_id) if body.address_id else None
    if address:
        owned(actor, address.user_id)
    await commerce.serviceable(db, branch, window, body.delivery_method, address, body.category_id)
    return {"serviceable": True}


@router.post("/orders/{order_id}/cancel", response_model=s.OrderOut, tags=["Commerce"])
async def cancel_order(order_id: UUID, body: s.VersionIn, actor: Actor, request: Request, db: DB):
    return await commerce.cancel_order(
        db, actor, order_id, body.expected_version, request.state.request_id
    )


@router.get("/notifications", response_model=s.Page[s.StateOut], tags=["Operations"])
async def notifications(actor: Actor, db: DB, cursor: str | None = None, limit: Limit = 50):
    model = F["operations.notification_jobs"]
    return await page(db, model, [model.user_id == UUID(actor.subject)], s.StateOut, cursor, limit)


def _bulk_job_out(job):
    return {
        "id": str(job.id),
        "entity": job.kind,
        "status": job.status,
        "row_count": job.row_count,
        "valid_count": job.valid_count,
        "created_count": job.created_count,
        "failed_count": job.failed_count,
        "previewed": job.previewed_at is not None,
        "created_at": job.created_at.isoformat(),
    }


async def _owned_bulk_job(db, actor, job_id, lock=False):
    statement = select(m.BulkJob).where(
        m.BulkJob.id == job_id, m.BulkJob.actor_id == UUID(actor.subject)
    )
    if lock:
        statement = statement.with_for_update()
    job = await db.scalar(statement)
    if job is None:
        raise BusinessError("bulk_job_not_found", "Bulk job was not found", 404)
    return job


async def _validate_branch_job(db, actor, job):
    rows = (
        await db.scalars(
            select(m.BulkJobRow)
            .where(m.BulkJobRow.job_id == job.id)
            .order_by(m.BulkJobRow.row_number)
        )
    ).all()
    seen = set()
    valid = failed = 0
    for row in rows:
        payload = bulk_data.apply_mapping(row.raw_payload, job.mapping)
        errors = []
        warnings = []
        source_key = payload["external_ref"].strip()
        if not source_key or len(source_key) > 200:
            errors.append({"field": "external_ref", "code": "required_or_too_long"})
        if source_key and source_key in seen:
            errors.append({"field": "external_ref", "code": "duplicate_in_file"})
        if source_key:
            seen.add(source_key)
        if not payload["branch_name"] or len(payload["branch_name"]) > 200:
            errors.append({"field": "branch_name", "code": "required_or_too_long"})
        if payload["branch_name"].lstrip()[:1] in {"=", "+", "-", "@"}:
            errors.append({"field": "branch_name", "code": "unsafe_spreadsheet_formula"})
        try:
            brand_id = UUID(payload["brand_id"])
        except (ValueError, TypeError):
            brand_id = None
            errors.append({"field": "brand_id", "code": "invalid_uuid"})
        try:
            city_id = UUID(payload["city_id"])
        except (ValueError, TypeError):
            city_id = None
            errors.append({"field": "city_id", "code": "invalid_uuid"})
        try:
            latitude = Decimal(payload["latitude"])
            if (
                not latitude.is_finite()
                or not -90 <= latitude <= 90
                or latitude.as_tuple().exponent < -7
                or latitude.adjusted() > 2
            ):
                raise ValueError
        except (ValueError, ArithmeticError):
            latitude = None
            errors.append({"field": "latitude", "code": "out_of_range"})
        try:
            longitude = Decimal(payload["longitude"])
            if (
                not longitude.is_finite()
                or not -180 <= longitude <= 180
                or longitude.as_tuple().exponent < -7
                or longitude.adjusted() > 2
            ):
                raise ValueError
        except (ValueError, ArithmeticError):
            longitude = None
            errors.append({"field": "longitude", "code": "out_of_range"})
        brand = await db.get(m.Brand, brand_id) if brand_id else None
        city = await db.get(m.City, city_id) if city_id else None
        authorized_scope = False
        if not brand or not city or not city.active:
            if brand_id and city_id:
                errors.append({"field": "references", "code": "unavailable"})
        elif not any(error["field"] in {"brand_id", "city_id"} for error in errors):
            try:
                await scoped(db, actor, "merchant.write", brand.organization_id, city.id)
                authorized_scope = True
            except BusinessError:
                errors.append({"field": "references", "code": "unavailable"})
        if source_key and authorized_scope:
            reference = await db.scalar(
                select(m.BulkExternalRef.id).where(
                    m.BulkExternalRef.entity == "branch", m.BulkExternalRef.source_key == source_key
                )
            )
            if reference:
                errors.append({"field": "external_ref", "code": "already_imported"})
        if authorized_scope and brand and city and payload["branch_name"]:
            duplicate = await db.scalar(
                select(m.Branch.id)
                .where(
                    m.Branch.brand_id == brand.id,
                    m.Branch.city_id == city.id,
                    func.lower(m.Branch.name) == payload["branch_name"].lower(),
                )
                .limit(1)
            )
            if duplicate:
                warnings.append({"field": "branch_name", "code": "possible_existing_branch"})
        row.payload = {
            **payload,
            "brand_id": str(brand_id) if brand_id else "",
            "city_id": str(city_id) if city_id else "",
            "latitude": str(latitude) if latitude is not None else "",
            "longitude": str(longitude) if longitude is not None else "",
        }
        row.errors = errors + warnings
        row.status = "valid" if not errors else "invalid"
        valid += int(not errors)
        failed += int(bool(errors))
    job.valid_count = valid
    job.failed_count = failed
    job.status = "VALIDATED"
    return rows


@router.get("/bulk/templates/{entity}", tags=["Bulk data"])
async def bulk_template(entity: str):
    if entity != "branches":
        raise BusinessError("template_not_found", "Only branch onboarding CSV is available", 404)
    content = "external_ref,brand_id,city_id,branch_name,latitude,longitude\n"
    return Response(
        content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="quickbuddy-branches-template.csv"'},
    )


@router.post(
    "/bulk/imports",
    status_code=201,
    tags=["Bulk data"],
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"text/csv": {"schema": {"type": "string"}}},
        }
    },
)
async def create_bulk_import(
    request: Request,
    actor: Actor,
    db: DB,
    idempotency_key: Key,
    entity: Annotated[str, Header(alias="X-Bulk-Entity")],
):
    await actor_budget(request, actor, "bulk-import", 10)
    if entity != "branches":
        raise BusinessError("bulk_entity_not_supported", "Only branch onboarding is enabled", 422)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise BusinessError("invalid_content_length", "Invalid content length", 400) from exc
        if declared_length < 0 or declared_length > bulk_data.MAX_UPLOAD_BYTES:
            raise BusinessError("bulk_file_size", "CSV is limited to 5 MiB", 413)
    permission = await db.scalar(
        select(func.count())
        .select_from(m.RoleAssignment)
        .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
        .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
        .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
        .where(
            m.RoleAssignment.user_id == UUID(actor.subject),
            m.Permission.code == "merchant.write",
        )
    )
    if not permission:
        raise BusinessError("forbidden", "Merchant write permission is required", 403)
    if not request.headers.get("content-type", "").lower().startswith("text/csv"):
        raise BusinessError("bulk_content_type", "Upload a CSV file as text/csv", 415)
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > bulk_data.MAX_UPLOAD_BYTES:
            raise BusinessError("bulk_file_size", "CSV is limited to 5 MiB", 413)
    source_hash = hashlib.sha256(content).hexdigest()
    existing = await db.scalar(
        select(m.BulkJob).where(
            m.BulkJob.actor_id == UUID(actor.subject), m.BulkJob.idempotency_key == idempotency_key
        )
    )
    if existing:
        if existing.source_hash != source_hash or existing.kind != entity:
            raise BusinessError(
                "idempotency_conflict", "Idempotency key was used for another file", 409
            )
        return _bulk_job_out(existing)
    recent_jobs = await db.scalar(
        select(func.count())
        .select_from(m.BulkJob)
        .where(
            m.BulkJob.actor_id == UUID(actor.subject),
            m.BulkJob.created_at >= now() - timedelta(hours=1),
        )
    )
    if recent_jobs >= 20:
        raise BusinessError("bulk_rate_limited", "Import job limit reached; retry later", 429)
    headers, source_rows = bulk_data.parse_csv(bytes(content))
    if not source_rows:
        raise BusinessError("bulk_empty_file", "CSV must contain at least one data row", 422)
    job = await add(
        db,
        m.BulkJob,
        actor_id=UUID(actor.subject),
        kind=entity,
        status="VALIDATED",
        idempotency_key=idempotency_key,
        source_hash=source_hash,
        row_count=len(source_rows),
        mapping={field: field for field in bulk_data.BRANCH_FIELDS},
    )
    for row_number, row_payload in enumerate(source_rows, start=2):
        canonical = bulk_data.apply_mapping(row_payload, {})
        await add(
            db,
            m.BulkJobRow,
            job_id=job.id,
            row_number=row_number,
            source_key=canonical.get("external_ref", "") or f"row-{row_number}",
            raw_payload=row_payload,
            payload=canonical,
            errors=[],
            status="valid",
        )
    await _validate_branch_job(db, actor, job)
    await audit(
        db,
        actor,
        "bulk.import.created",
        job.id,
        request.state.request_id,
        current=job.status,
        version=1,
    )
    return _bulk_job_out(job)


@router.post("/bulk/imports/{job_id}/mapping", tags=["Bulk data"])
async def map_bulk_import(
    job_id: UUID, body: s.BulkMappingIn, request: Request, actor: Actor, db: DB
):
    job = await _owned_bulk_job(db, actor, job_id, lock=True)
    if job.status != "VALIDATED" or job.previewed_at is not None:
        raise BusinessError("bulk_job_locked", "Mapping is locked after preview or commit", 409)
    rows = (
        await db.scalars(select(m.BulkJobRow).where(m.BulkJobRow.job_id == job.id).limit(1))
    ).first()
    headers = list(rows.raw_payload) if rows else []
    job.mapping = bulk_data.validate_mapping(body.mapping, headers)
    await _validate_branch_job(db, actor, job)
    await audit(
        db,
        actor,
        "bulk.import.mapped",
        job.id,
        request.state.request_id,
        current="mapped",
        version=1,
    )
    return _bulk_job_out(job)


@router.post("/bulk/imports/{job_id}/validate", tags=["Bulk data"])
async def validate_bulk_import(job_id: UUID, request: Request, actor: Actor, db: DB):
    job = await _owned_bulk_job(db, actor, job_id, lock=True)
    if job.status != "VALIDATED" or job.previewed_at is not None:
        raise BusinessError("bulk_job_locked", "Only uncommitted jobs can be validated", 409)
    await _validate_branch_job(db, actor, job)
    await audit(
        db,
        actor,
        "bulk.import.validated",
        job.id,
        request.state.request_id,
        current=job.status,
        version=1,
    )
    return _bulk_job_out(job)


@router.post("/bulk/imports/{job_id}/dry-run", tags=["Bulk data"])
async def preview_bulk_import(job_id: UUID, request: Request, actor: Actor, db: DB):
    job = await _owned_bulk_job(db, actor, job_id, lock=True)
    if job.status != "VALIDATED":
        raise BusinessError("bulk_job_locked", "Only validated jobs can be previewed", 409)
    job.previewed_at = now()
    await audit(
        db,
        actor,
        "bulk.import.previewed",
        job.id,
        request.state.request_id,
        current="previewed",
        version=1,
    )
    rows = (
        await db.scalars(
            select(m.BulkJobRow)
            .where(m.BulkJobRow.job_id == job.id)
            .order_by(m.BulkJobRow.row_number)
            .limit(100)
        )
    ).all()
    return {
        **_bulk_job_out(job),
        "rows": [
            {
                "row_number": row.row_number,
                "status": row.status,
                "external_ref": row.payload.get("external_ref", ""),
                "branch_name": row.payload.get("branch_name", ""),
                "issues": row.errors,
            }
            for row in rows
        ],
        "truncated": job.row_count > len(rows),
    }


@router.post("/bulk/imports/{job_id}/commit", tags=["Bulk data"])
async def commit_bulk_import(job_id: UUID, request: Request, actor: Actor, db: DB):
    job = await _owned_bulk_job(db, actor, job_id, lock=True)
    if job.status in {"COMPLETED", "PARTIALLY_COMPLETED"}:
        return _bulk_job_out(job)
    if job.status != "VALIDATED" or job.previewed_at is None:
        raise BusinessError("bulk_preview_required", "Validate and preview the import first", 409)
    if job.valid_count > 200:
        raise BusinessError("bulk_chunk_limit", "Synchronous commit is limited to 200 rows", 422)
    rows = (
        await db.scalars(
            select(m.BulkJobRow)
            .where(m.BulkJobRow.job_id == job.id, m.BulkJobRow.status == "valid")
            .order_by(m.BulkJobRow.row_number)
            .with_for_update()
        )
    ).all()
    created = failed = 0
    for row in rows:
        payload = row.payload
        brand_id, city_id = UUID(payload["brand_id"]), UUID(payload["city_id"])
        brand = await db.get(m.Brand, brand_id)
        city = await db.get(m.City, city_id)
        if not brand or not city or not city.active:
            row.status = "invalid"
            row.errors = [{"field": "reference", "code": "changed_since_preview"}]
            failed += 1
            continue
        await scoped(db, actor, "merchant.write", brand.organization_id, city.id)
        branch_id = uuid4()
        ref_id = await db.scalar(
            insert(m.BulkExternalRef)
            .values(
                id=uuid4(), entity="branch", source_key=payload["external_ref"], record_id=branch_id
            )
            .on_conflict_do_nothing(index_elements=["entity", "source_key"])
            .returning(m.BulkExternalRef.id)
        )
        if ref_id is None:
            row.status = "conflict"
            row.errors = [{"field": "external_ref", "code": "already_imported"}]
            failed += 1
            continue
        await add(
            db,
            m.Branch,
            id=branch_id,
            brand_id=brand.id,
            organization_id=brand.organization_id,
            city_id=city.id,
            name=payload["branch_name"],
            latitude=Decimal(payload["latitude"]),
            longitude=Decimal(payload["longitude"]),
            status="pending",
            accepting_orders=False,
            version=1,
        )
        await audit(
            db,
            actor,
            "merchant.branch.bulk_created",
            branch_id,
            request.state.request_id,
            organization_id=brand.organization_id,
            current="pending",
            version=1,
        )
        row.status = "committed"
        row.record_id = branch_id
        created += 1
    job.created_count = created
    job.failed_count += failed
    job.status = "COMPLETED" if failed == 0 else "PARTIALLY_COMPLETED" if created else "FAILED"
    await audit(
        db,
        actor,
        "bulk.import.committed",
        job.id,
        request.state.request_id,
        current=job.status,
        version=2,
    )
    return _bulk_job_out(job)


@router.get("/bulk/imports/{job_id}", tags=["Bulk data"])
async def get_bulk_import(job_id: UUID, actor: Actor, db: DB):
    return _bulk_job_out(await _owned_bulk_job(db, actor, job_id))


@router.get("/bulk/imports/{job_id}/errors", tags=["Bulk data"])
async def get_bulk_import_errors(job_id: UUID, actor: Actor, db: DB, limit: int = 100):
    if limit < 1 or limit > 500:
        raise BusinessError("invalid_limit", "Error page limit must be from 1 to 500", 422)
    job = await _owned_bulk_job(db, actor, job_id)
    rows = (
        await db.scalars(
            select(m.BulkJobRow)
            .where(m.BulkJobRow.job_id == job.id, m.BulkJobRow.errors != [])
            .order_by(m.BulkJobRow.row_number)
            .limit(limit)
        )
    ).all()
    return {"items": [{"row_number": row.row_number, "issues": row.errors} for row in rows]}


@router.get("/bulk/jobs", tags=["Bulk data"])
async def list_bulk_jobs(actor: Actor, db: DB, limit: int = 50):
    if limit < 1 or limit > 100:
        raise BusinessError("invalid_limit", "Job limit must be from 1 to 100", 422)
    rows = (
        await db.scalars(
            select(m.BulkJob)
            .where(m.BulkJob.actor_id == UUID(actor.subject))
            .order_by(m.BulkJob.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {"items": [_bulk_job_out(job) for job in rows]}


@router.post("/bulk/jobs/{job_id}/cancel", tags=["Bulk data"])
async def cancel_bulk_job(job_id: UUID, request: Request, actor: Actor, db: DB):
    job = await _owned_bulk_job(db, actor, job_id, lock=True)
    if job.status != "VALIDATED":
        raise BusinessError(
            "bulk_job_not_cancellable", "Only uncommitted jobs can be cancelled", 409
        )
    job.status = "CANCELLED"
    await audit(
        db,
        actor,
        "bulk.import.cancelled",
        job.id,
        request.state.request_id,
        current=job.status,
        version=1,
    )
    return _bulk_job_out(job)


@router.post("/bulk/exports", tags=["Bulk data"])
async def export_branches(body: s.BulkExportIn, request: Request, actor: Actor, db: DB):
    await actor_budget(request, actor, "bulk-export", 10)
    rows = (
        await db.execute(
            select(m.Branch, m.Brand.merchant_type)
            .join(m.Brand, m.Brand.id == m.Branch.brand_id)
            .where(m.Branch.city_id == body.city_id)
            .order_by(m.Branch.created_at.desc())
            .limit(body.limit + 1)
        )
    ).all()
    if len(rows) > body.limit:
        raise BusinessError(
            "export_limit", "Filter results to at most 500 branches per export", 413
        )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "branch_id",
            "organization_id",
            "brand_id",
            "city_id",
            "branch_name",
            "merchant_type",
            "status",
            "accepting_orders",
            "latitude",
            "longitude",
        ]
    )
    exported = 0
    for branch, merchant_type in rows:
        try:
            await scoped(
                db, actor, "merchant.export", branch.organization_id, branch.city_id, branch.id
            )
        except BusinessError:
            continue
        # CSV formula escaping applies to text fields; IDs/numbers remain unchanged.
        text_values = [branch.name, merchant_type, branch.status]
        safe = ["'" + value if value[:1] in "=+-@" else value for value in text_values]
        writer.writerow(
            [
                str(branch.id),
                str(branch.organization_id),
                str(branch.brand_id),
                str(branch.city_id),
                safe[0],
                safe[1],
                safe[2],
                branch.accepting_orders,
                branch.latitude,
                branch.longitude,
            ]
        )
        exported += 1
    if not exported:
        raise BusinessError("forbidden", "No branches are available in this authorized scope", 403)
    await audit(
        db,
        actor,
        "bulk.export.branches",
        body.city_id,
        request.state.request_id,
        current=f"rows:{exported}",
        version=1,
    )
    stamp = now().strftime("%Y%m%dT%H%M%SZ")
    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="quickbuddy-branches-{stamp}.csv"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/admin/customers", tags=["Customer administration"])
async def admin_customers(
    actor: Actor,
    db: DB,
    city_id: UUID,
    q: str | None = Query(default=None, max_length=80),
    status: str | None = Query(default=None, pattern="^(active|restricted|suspended|pending)$"),
    after: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    global_access, organization_ids, city_ids = await customer_admin.customer_scope(db, actor)
    if not global_access and city_id not in city_ids:
        # Organization-scoped administrators may select only cities containing their own orders.
        if not organization_ids:
            raise BusinessError("forbidden", "City is outside customer administration scope", 403)
    return await customer_admin.list_customers(
        db,
        global_access=global_access,
        organization_ids=organization_ids,
        city_ids=city_ids,
        city_id=city_id,
        query=q,
        status=status,
        limit=limit,
        after=after,
    )


async def _admin_customer_scope(db, actor, customer_id):
    global_access, organization_ids, city_ids = await customer_admin.customer_scope(db, actor)
    customer = await customer_admin.require_customer(
        db,
        customer_id,
        global_access=global_access,
        organization_ids=organization_ids,
        city_ids=city_ids,
    )
    return customer, global_access, organization_ids, city_ids


def _customer_order_scope(global_access, organization_ids, city_ids):
    stmt = (
        select(m.Order)
        .join(m.MerchantOrder, m.MerchantOrder.order_id == m.Order.id)
        .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
    )
    scope_filter = customer_admin._scope_filter(m.Branch, global_access, organization_ids, city_ids)
    stmt = stmt.where(scope_filter) if scope_filter is not None else stmt
    return stmt.distinct()


@router.get("/admin/customers/{customer_id}", tags=["Customer administration"])
async def admin_customer_360(customer_id: UUID, request: Request, actor: Actor, db: DB):
    customer, global_access, organization_ids, city_ids = await _admin_customer_scope(
        db, actor, customer_id
    )
    order_rows = (
        _customer_order_scope(global_access, organization_ids, city_ids)
        .where(m.Order.user_id == customer_id)
        .subquery()
    )
    summary = (
        await db.execute(
            select(
                func.count(order_rows.c.id),
                func.count(order_rows.c.id).filter(order_rows.c.status == "completed"),
                func.coalesce(func.sum(order_rows.c.total), 0),
                func.max(order_rows.c.created_at),
            )
        )
    ).one()
    order_count, completed_count, gross_value, last_order_at = summary
    loyalty = F["engagement.loyalty_accounts"]
    points = await db.scalar(
        select(func.coalesce(func.sum(loyalty.points), 0)).where(loyalty.user_id == customer_id)
    )
    refunds = (
        await db.scalar(
            select(func.coalesce(func.sum(m.Refund.amount), 0))
            .join(m.PaymentIntent, m.PaymentIntent.id == m.Refund.payment_id)
            .join(m.Order, m.Order.id == m.PaymentIntent.order_id)
            .where(m.Order.user_id == customer_id, m.Order.id.in_(select(order_rows.c.id)))
        )
    ) or 0
    await audit(
        db,
        actor,
        "customer.360.read",
        customer_id,
        request.state.request_id,
        current="summary",
        version=1,
    )
    return {
        "customer": customer,
        "summary": {
            "order_count": int(order_count or 0),
            "completed_order_count": int(completed_count or 0),
            "order_frequency": "historical completed order count; interval not estimated",
            "gross_purchase_value": str(gross_value or 0),
            "refund_total": str(refunds),
            "historical_contribution": None,
            "historical_contribution_note": (
                "Not calculated: attributable platform/service costs are not modeled here."
            ),
            "last_order_at": last_order_at.isoformat() if last_order_at else None,
            "loyalty_points_balance": int(points or 0),
        },
        "tabs": [
            "overview",
            "orders",
            "payments",
            "addresses",
            "subscriptions",
            "loyalty",
            "referrals",
            "campaigns",
            "support",
            "feedback",
            "privacy",
            "security",
        ],
    }


@router.get("/admin/customers/{customer_id}/orders", tags=["Customer administration"])
async def admin_customer_orders(
    customer_id: UUID,
    actor: Actor,
    db: DB,
    after: UUID | None = None,
    limit: int = Query(default=25, ge=1, le=100),
):
    _, global_access, organization_ids, city_ids = await _admin_customer_scope(
        db, actor, customer_id
    )
    stmt = _customer_order_scope(global_access, organization_ids, city_ids).where(
        m.Order.user_id == customer_id
    )
    if after:
        stmt = stmt.where(m.Order.id < after)
    rows = (await db.scalars(stmt.order_by(m.Order.id.desc()).limit(limit + 1))).all()
    more = len(rows) > limit
    rows = rows[:limit]
    return {
        "items": [
            {
                "id": str(row.id),
                "status": row.status,
                "total": str(row.total),
                "currency": row.currency,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ],
        "next_cursor": str(rows[-1].id) if more else None,
    }


@router.get("/admin/customers/{customer_id}/loyalty", tags=["Customer administration"])
async def admin_customer_loyalty(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    account = F["engagement.loyalty_accounts"]
    transaction = F["engagement.loyalty_transactions"]
    accounts = (
        await db.execute(
            select(account.id, account.program_code, account.points, account.created_at)
            .where(account.user_id == customer_id)
            .order_by(account.created_at.desc())
            .limit(limit)
        )
    ).all()
    history = (
        await db.execute(
            select(transaction.points, transaction.order_id, transaction.created_at)
            .join(account, account.id == transaction.account_id)
            .where(account.user_id == customer_id)
            .order_by(transaction.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "accounts": [
            {
                "id": str(aid),
                "program": code,
                "points_balance": points,
                "created_at": created.isoformat(),
            }
            for aid, code, points, created in accounts
        ],
        "transactions": [
            {
                "points": points,
                "order_id": str(order_id) if order_id else None,
                "created_at": created.isoformat(),
            }
            for points, order_id, created in history
        ],
    }


@router.get("/admin/customers/{customer_id}/subscriptions", tags=["Customer administration"])
async def admin_customer_subscriptions(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    subscription = F["engagement.customer_subscriptions"]
    plan = F["engagement.subscription_plans"]
    rows = (
        await db.execute(
            select(
                subscription.id,
                plan.name,
                subscription.status,
                subscription.starts_at,
                subscription.ends_at,
            )
            .join(plan, plan.id == subscription.plan_id)
            .where(subscription.user_id == customer_id)
            .order_by(subscription.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": str(sid),
                "plan": name,
                "status": status,
                "starts_at": start.isoformat(),
                "ends_at": end.isoformat() if end else None,
            }
            for sid, name, status, start, end in rows
        ]
    }


@router.get("/admin/customers/{customer_id}/support", tags=["Customer administration"])
async def admin_customer_support(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    rows = (
        await db.scalars(
            select(m.Ticket)
            .where(m.Ticket.user_id == customer_id)
            .order_by(m.Ticket.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": str(row.id),
                "subject": row.subject,
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.get("/admin/customers/{customer_id}/feedback", tags=["Customer administration"])
async def admin_customer_feedback(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    review = F["engagement.reviews"]
    rows = (
        await db.execute(
            select(
                review.id,
                review.order_item_id,
                review.rating,
                review.moderation_status,
                review.created_at,
            )
            .where(review.user_id == customer_id)
            .order_by(review.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": str(rid),
                "order_item_id": str(item_id),
                "rating": rating,
                "moderation_status": state,
                "created_at": created.isoformat(),
            }
            for rid, item_id, rating, state, created in rows
        ]
    }


@router.get("/admin/customers/{customer_id}/payments", tags=["Customer administration"])
async def admin_customer_payments(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    _, global_access, organization_ids, city_ids = await _admin_customer_scope(
        db, actor, customer_id
    )
    scoped_orders = (
        _customer_order_scope(global_access, organization_ids, city_ids)
        .where(m.Order.user_id == customer_id)
        .subquery()
    )
    payments = (
        (
            await db.execute(
                select(m.PaymentIntent)
                .where(m.PaymentIntent.order_id.in_(select(scoped_orders.c.id)))
                .order_by(m.PaymentIntent.created_at.desc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )
    payment_ids = [row.id for row in payments]
    refunds = []
    if payment_ids:
        refunds = (
            await db.scalars(
                select(m.Refund)
                .where(m.Refund.payment_id.in_(payment_ids))
                .order_by(m.Refund.created_at.desc())
                .limit(limit)
            )
        ).all()
    return {
        "items": [
            {
                "id": str(row.id),
                "order_id": str(row.order_id),
                "status": row.status,
                "amount": str(row.amount),
                "refunded": str(row.refunded),
                "currency": row.currency,
                "created_at": row.created_at.isoformat(),
            }
            for row in payments
        ],
        "refunds": [
            {
                "payment_id": str(row.payment_id),
                "amount": str(row.amount),
                "status": row.status,
                "created_at": row.created_at.isoformat(),
            }
            for row in refunds
        ],
    }


@router.get("/admin/customers/{customer_id}/addresses", tags=["Customer administration"])
async def admin_customer_addresses(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    rows = (
        await db.execute(
            select(m.Address.id, m.Address.label, m.City.name, m.Address.created_at)
            .join(m.City, m.City.id == m.Address.city_id)
            .where(m.Address.user_id == customer_id)
            .order_by(m.Address.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {"id": str(address_id), "label": label, "city": city, "created_at": created.isoformat()}
            for address_id, label, city, created in rows
        ],
        "address_text_and_coordinates": "withheld from the CRM summary",
    }


@router.get("/admin/customers/{customer_id}/referrals", tags=["Customer administration"])
async def admin_customer_referrals(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    referral = F["engagement.referrals"]
    program = F["engagement.referral_programs"]
    rows = (
        await db.execute(
            select(
                program.name,
                referral.status,
                referral.created_at,
                referral.referrer_id == customer_id,
            )
            .join(program, program.id == referral.program_id)
            .where(
                or_(referral.referrer_id == customer_id, referral.referred_user_id == customer_id)
            )
            .order_by(referral.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "program": name,
                "status": status,
                "direction": "referred" if is_referrer else "invited",
                "created_at": created.isoformat(),
            }
            for name, status, created, is_referrer in rows
        ]
    }


@router.get("/admin/customers/{customer_id}/campaigns", tags=["Customer administration"])
async def admin_customer_campaigns(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    redemption = F["engagement.coupon_redemptions"]
    coupon = F["engagement.coupons"]
    campaign = F["engagement.promotional_campaigns"]
    rows = (
        await db.execute(
            select(campaign.name, redemption.amount, redemption.created_at)
            .join(coupon, coupon.id == redemption.coupon_id)
            .join(campaign, campaign.id == coupon.campaign_id)
            .where(redemption.user_id == customer_id)
            .order_by(redemption.created_at.desc())
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {"campaign": name, "redeemed_amount": str(amount), "created_at": created.isoformat()}
            for name, amount, created in rows
        ]
    }


@router.get("/admin/customers/{customer_id}/privacy", tags=["Customer administration"])
async def admin_customer_privacy(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=50, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    notification = F["engagement.notification_preferences"]
    preferences = F["engagement.customer_preferences"]
    channels = (
        await db.execute(
            select(notification.channel, notification.enabled)
            .where(notification.user_id == customer_id)
            .limit(limit)
        )
    ).all()
    keys = (
        await db.scalars(
            select(preferences.preference_key)
            .where(preferences.user_id == customer_id)
            .limit(limit)
        )
    ).all()
    consent_events = (
        await db.scalars(
            select(m.CustomerConsentEvent)
            .where(m.CustomerConsentEvent.user_id == customer_id)
            .order_by(m.CustomerConsentEvent.created_at.desc(), m.CustomerConsentEvent.id.desc())
            .limit(limit)
        )
    ).all()
    latest_consents = {}
    for event_row in consent_events:
        latest_consents.setdefault(
            (event_row.purpose, event_row.channel),
            {
                "purpose": event_row.purpose,
                "channel": event_row.channel,
                "enabled": event_row.enabled,
                "policy_version": event_row.policy_version,
                "recorded_at": event_row.created_at.isoformat(),
            },
        )
    return {
        "notification_preferences": [
            {"channel": channel, "enabled": enabled} for channel, enabled in channels
        ],
        "preference_keys": list(keys),
        "marketing_consent_evidence": list(latest_consents.values()),
        "notice": (
            "Only explicit customer-authored ledger events are consent evidence; "
            "notification preferences are shown separately."
        ),
    }


@router.get("/admin/customers/{customer_id}/security", tags=["Customer administration"])
async def admin_customer_security(
    customer_id: UUID, actor: Actor, db: DB, limit: int = Query(default=25, ge=1, le=100)
):
    await _admin_customer_scope(db, actor, customer_id)
    authentication_event = F["identity.authentication_events"]
    rows = (
        await db.execute(
            select(authentication_event.event_type, authentication_event.created_at)
            .where(authentication_event.user_id == customer_id)
            .order_by(authentication_event.created_at.desc())
            .limit(limit)
        )
    ).all()
    sessions = await db.scalar(
        select(func.count(m.Session.id)).where(
            m.Session.user_id == customer_id,
            m.Session.revoked_at.is_(None),
            m.Session.expires_at > now(),
        )
    )
    return {
        "active_session_count": int(sessions or 0),
        "events": [
            {"type": event_type, "created_at": created.isoformat()} for event_type, created in rows
        ],
    }


@router.get("/admin/customers-export", tags=["Customer administration"])
async def admin_customer_export(
    request: Request,
    actor: Actor,
    db: DB,
    city_id: UUID,
    purpose: str = Query(
        default="customer_directory",
        pattern="^(customer_directory|support_followup|retention_review)$",
    ),
    limit: int = Query(default=500, ge=1, le=500),
):
    await actor_budget(request, actor, "customer-export", 10)
    global_access, organization_ids, city_ids = await customer_admin.customer_scope(db, actor)
    if not global_access and city_id not in city_ids and not organization_ids:
        raise BusinessError("forbidden", "City is outside customer administration scope", 403)
    result = await customer_admin.list_customers(
        db,
        global_access=global_access,
        organization_ids=organization_ids,
        city_ids=city_ids,
        city_id=city_id,
        limit=limit,
    )
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "customer_id",
            "name",
            "status",
            "masked_email",
            "email_verified",
            "masked_phone",
            "phone_verified",
            "order_count",
            "completed_order_count",
            "historical_gross_purchase_value",
            "last_order_at",
        ]
    )
    for row in result["items"]:
        values = [row["name"] or "", row["status"], row["email"] or "", row["phone"] or ""]
        safe = ["'" + value if value[:1] in "=+-@" else value for value in values]
        writer.writerow(
            [
                row["id"],
                safe[0],
                safe[1],
                safe[2],
                row["email_verified"],
                safe[3],
                row["phone_verified"],
                row["order_count"],
                row["completed_order_count"],
                row["gross_purchase_value"],
                row["last_order_at"] or "",
            ]
        )
    exported = len(result["items"])
    await audit(
        db,
        actor,
        "customer.export",
        city_id,
        request.state.request_id,
        current=f"rows:{exported};purpose:{purpose}",
        version=1,
    )
    stamp = now().strftime("%Y%m%dT%H%M%SZ")
    return StreamingResponse(
        iter(["\ufeff" + output.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="quickbuddy-customers-{stamp}.csv"',
            "Cache-Control": "private, no-store",
        },
    )


@router.post("/admin/customer-segments/preview", tags=["Customer administration"])
async def preview_customer_segment(
    body: s.CustomerSegmentPreviewIn,
    request: Request,
    actor: Actor,
    db: DB,
):
    await actor_budget(request, actor, "customer-segment-preview", 20)
    global_access, organization_ids, city_ids = await customer_admin.customer_scope(db, actor)
    if not global_access and body.city_id not in city_ids and not organization_ids:
        raise BusinessError("forbidden", "City is outside customer administration scope", 403)
    result = await customer_admin.preview_segment(
        db,
        city_id=body.city_id,
        global_access=global_access,
        organization_ids=organization_ids,
        city_ids=city_ids,
        logic=body.logic,
        conditions=body.conditions,
    )
    await audit(
        db,
        actor,
        "customer.segment.preview",
        body.city_id,
        request.state.request_id,
        current=f"matches:{result['matched_count']}",
        version=1,
    )
    return result
