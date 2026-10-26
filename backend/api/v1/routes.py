import base64
from datetime import timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.api.v1 import schemas as s
from backend.api.v1.dependencies import DB, Actor
from backend.application import commerce, finance, identity, logistics
from backend.application.common import add, audit, branch_scope, now, owned, scoped
from backend.domain.rules import BusinessError, money
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository

router = APIRouter(prefix="/api/v1")
Key = Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)]
Limit = Annotated[int, Query(ge=1, le=100)]


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


async def auth_budget(request, identity_key):
    # Separate committed transaction preserves failed login/OTP rate counters.
    async with request.app.state.sessions.begin() as db:
        allowed = await identity.rate_limit(
            db,
            identity_key,
            request.client.host if request.client else "unknown",
            limit=request.app.state.settings.auth_rate_limit_per_minute,
        )
    if not allowed:
        raise BusinessError(
            "rate_limited", "Authentication rate limit exceeded; retry after 60 seconds", 429
        )


@router.post("/auth/register", response_model=s.IdOut, status_code=201, tags=["Identity"])
async def register(body: s.RegisterIn, request: Request):
    await auth_budget(request, body.email.lower())
    async with request.app.state.sessions.begin() as db:
        return await identity.register(db, body.email, body.password.get_secret_value())


@router.post("/auth/login", response_model=s.TokenOut, tags=["Identity"])
async def login(body: s.LoginIn, request: Request):
    verifier = local_auth(request)
    await auth_budget(request, body.email.lower())
    async with request.app.state.sessions.begin() as db:
        result = await identity.login(db, verifier, body.email, body.password.get_secret_value())
    if result is None:
        raise BusinessError("invalid_credentials", "Invalid credentials", 401)
    return result


@router.post("/auth/refresh", response_model=s.TokenOut, tags=["Identity"])
async def refresh(body: s.RefreshIn, request: Request):
    verifier = local_auth(request)
    await auth_budget(request, "refresh:" + identity.digest(body.refresh_token.get_secret_value()))
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


@router.post("/auth/challenges", response_model=s.IdOut, status_code=201, tags=["Identity"])
async def challenge(body: s.OtpIn, actor: Actor, request: Request, db: DB):
    email = await db.scalar(select(m.Email.address).where(m.Email.user_id == UUID(actor.subject)))
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
    await auth_budget(request, "otp:" + actor.subject)
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
    "/organizations/{organization_id}/members",
    response_model=s.IdOut,
    status_code=201,
    tags=["Identity"],
)
async def member(organization_id: UUID, body: s.MemberIn, actor: Actor, db: DB):
    branch = await branch_scope(db, actor, body.branch_id, "organization.members")
    if branch.organization_id != organization_id:
        raise BusinessError("forbidden", "Branch is outside this organization", 403)
    await Repository(db).require(m.User, body.user_id)
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
    await add(
        db,
        m.RoleAssignment,
        organization_id=organization_id,
        user_id=body.user_id,
        role_id=role.id,
        branch_id=branch.id,
        city_id=branch.city_id,
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
async def city(body: s.CityIn, actor: Actor, db: DB):
    await scoped(db, actor, "geo.write")
    return await add(db, m.City, **body.model_dump())


@router.get("/geo/cities", response_model=s.Page[s.CityOut], tags=["Geography"])
async def cities(db: DB, cursor: str | None = None, limit: Limit = 50):
    return await page(db, m.City, [m.City.active.is_(True)], s.CityOut, cursor, limit)


@router.post("/geo/zones", response_model=s.NamedOut, status_code=201, tags=["Geography"])
async def zone(body: s.ZoneIn, actor: Actor, db: DB):
    await scoped(db, actor, "geo.write")
    return await add(db, m.Zone, **body.model_dump())


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
    predicates = [m.Branch.status == "approved", m.Branch.accepting_orders.is_(True)]
    if city_id:
        predicates.append(m.Branch.city_id == city_id)
    return await page(db, m.Branch, predicates, s.BranchOut, cursor, limit)


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
    return await page(db, m.Category, [], s.NamedOut, cursor, limit)


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
    return await add(db, m.Price, branch_id=branch_id, **body.model_dump())


@router.get(
    "/merchants/branches/{branch_id}/prices", response_model=s.Page[s.PriceOut], tags=["Catalogue"]
)
async def prices(branch_id: UUID, db: DB, cursor: str | None = None, limit: Limit = 50):
    branch = await Repository(db).require(m.Branch, branch_id)
    if branch.status != "approved":
        raise BusinessError("not_found", "Resource not found", 404)
    return await page(db, m.Price, [m.Price.branch_id == branch_id], s.PriceOut, cursor, limit)


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
    return await page(db, m.CartItem, [m.CartItem.cart_id == cart.id], s.CartItemOut, cursor, limit)


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
    return await commerce.make_quote(db, actor, cart_id)


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
    pilot.available = body.available
    return pilot


@router.put("/pilots/{pilot_id}/location", response_model=s.IdOut, tags=["Fulfillment"])
async def location(pilot_id: UUID, body: s.LocationIn, actor: Actor, db: DB):
    pilot = await Repository(db).require(m.Pilot, pilot_id)
    owned(actor, pilot.user_id)
    if body.observed_at.tzinfo is None or abs((now() - body.observed_at).total_seconds()) > 300:
        raise BusinessError(
            "invalid_location_time", "Location must have an offset and be within five minutes", 422
        )
    stmt = insert(m.LatestLocation).values(pilot_id=pilot_id, **body.model_dump())
    result = await db.scalar(
        stmt.on_conflict_do_update(
            index_elements=["pilot_id"],
            set_=body.model_dump(),
            where=m.LatestLocation.observed_at < body.observed_at,
        ).returning(m.LatestLocation.id)
    )
    if not result:
        result = await db.scalar(
            select(m.LatestLocation.id).where(m.LatestLocation.pilot_id == pilot_id)
        )
    await add(
        db,
        F["fulfillment.pilot_location_events"],
        pilot_id=pilot_id,
        **body.model_dump(),
        expires_at=now() + timedelta(days=7),
    )
    return {"id": result}


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


@router.post("/support/tickets", response_model=s.StateOut, status_code=201, tags=["Operations"])
async def ticket(body: s.TicketIn, actor: Actor, db: DB):
    if body.order_id:
        order = await Repository(db).require(m.Order, body.order_id)
        owned(actor, order.user_id)
    return await add(db, m.Ticket, user_id=UUID(actor.subject), **body.model_dump())


@router.post(
    "/support/tickets/{ticket_id}/messages",
    response_model=s.MessageOut,
    status_code=201,
    tags=["Operations"],
)
async def message(ticket_id: UUID, body: s.MessageIn, actor: Actor, db: DB):
    ticket = await Repository(db).require(m.Ticket, ticket_id)
    if str(ticket.user_id) != actor.subject:
        if ticket.organization_id is None:
            raise BusinessError("forbidden", "Ticket is not scoped to your organization", 403)
        await scoped(db, actor, "support.write", ticket.organization_id)
    return await add(
        db, m.TicketMessage, ticket_id=ticket.id, author_id=UUID(actor.subject), body=body.body
    )


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
