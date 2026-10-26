from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from uuid import UUID

from sqlalchemy import and_, exists, func, or_, select

from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def customer_scope(db, actor):
    """Return (global_access, organization_ids, city_ids) from current DB grants."""
    grants = (
        await db.execute(
            select(m.Role.name, m.RoleAssignment.organization_id, m.RoleAssignment.city_id)
            .join(m.RoleAssignment, m.RoleAssignment.role_id == m.Role.id)
            .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
            .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
            .where(
                m.RoleAssignment.user_id == UUID(actor.subject),
                m.Permission.code == "customer.read",
            )
        )
    ).all()
    if any(
        role == "platform_super_admin" and org is None and city is None
        for role, org, city in grants
    ):
        return True, set(), set()
    organization_ids = {org for _, org, _ in grants if org is not None}
    city_ids = {city for _, _, city in grants if city is not None}
    if organization_ids:
        memberships = set(
            (
                await db.scalars(
                    select(m.Membership.organization_id).where(
                        m.Membership.user_id == UUID(actor.subject),
                        m.Membership.status == "active",
                        m.Membership.organization_id.in_(organization_ids),
                    )
                )
            ).all()
        )
        organization_ids &= memberships
    if not organization_ids and not city_ids:
        raise BusinessError("forbidden", "Customer administration scope is required", 403)
    return False, organization_ids, city_ids


def _scope_filter(branch, global_access, organization_ids, city_ids):
    if global_access:
        return None
    filters = []
    if organization_ids:
        filters.append(branch.organization_id.in_(organization_ids))
    if city_ids:
        filters.append(branch.city_id.in_(city_ids))
    return or_(*filters)


def _mask_email(value):
    if not value or "@" not in value:
        return None
    local, domain = value.split("@", 1)
    return f"{local[:1]}***@{domain}"


def _mask_phone(value):
    if not value:
        return None
    return "***" + value[-4:]


def _customer_query(global_access, organization_ids, city_ids, city_id):
    Profile = F["identity.user_profiles"]
    Phone = F["identity.user_phone_numbers"]
    Email = m.Email
    order_stmt = (
        select(
            m.Order.id.label("id"),
            m.Order.user_id.label("user_id"),
            m.Order.status.label("status"),
            m.Order.total.label("total"),
            m.Order.created_at.label("created_at"),
        )
        .join(m.MerchantOrder, m.MerchantOrder.order_id == m.Order.id)
        .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
    )
    scope_filter = _scope_filter(m.Branch, global_access, organization_ids, city_ids)
    if scope_filter is not None:
        order_stmt = order_stmt.where(scope_filter)
    if city_id is not None:
        order_stmt = order_stmt.where(m.Branch.city_id == city_id)
    scoped_order_rows = order_stmt.distinct().subquery()
    orders = (
        select(
            scoped_order_rows.c.user_id,
            func.count(scoped_order_rows.c.id).label("order_count"),
            func.count(scoped_order_rows.c.id)
            .filter(scoped_order_rows.c.status == "completed")
            .label("completed_count"),
            func.sum(scoped_order_rows.c.total).label("gross_value"),
            func.max(scoped_order_rows.c.created_at).label("last_order_at"),
        )
        .group_by(scoped_order_rows.c.user_id)
        .subquery()
    )
    return Profile, Phone, Email, orders


async def list_customers(
    db,
    *,
    global_access,
    organization_ids,
    city_ids,
    city_id,
    query=None,
    status=None,
    limit=50,
    after=None,
):
    Profile, Phone, Email, orders = _customer_query(
        global_access, organization_ids, city_ids, city_id
    )
    display_name = func.coalesce(
        Profile.display_name,
        func.split_part(Email.address, "@", 1),
        "Customer",
    )
    stmt = (
        select(
            m.User,
            display_name,
            Email.address,
            Email.verified_at,
            Phone.e164,
            Phone.verified_at,
            orders.c.order_count,
            orders.c.completed_count,
            orders.c.gross_value,
            orders.c.last_order_at,
        )
        .outerjoin(Profile, Profile.user_id == m.User.id)
        .outerjoin(Email, Email.user_id == m.User.id)
        .outerjoin(Phone, Phone.user_id == m.User.id)
        .outerjoin(orders, orders.c.user_id == m.User.id)
        .where(
            m.User.status != "deleted",
            exists(
                select(m.RoleAssignment.id)
                .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
                .where(m.RoleAssignment.user_id == m.User.id, m.Role.name == "customer")
            ),
        )
    )
    if not global_access:
        stmt = stmt.where(orders.c.user_id.is_not(None))
    if city_id:
        if not global_access and city_id not in city_ids:
            # Company-level grants may be broad; constrain them to actual order city below.
            pass
        city_orders = (
            select(m.Order.user_id)
            .join(m.MerchantOrder, m.MerchantOrder.order_id == m.Order.id)
            .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
            .where(m.Branch.city_id == city_id)
        )
        if not global_access:
            city_orders = city_orders.where(
                _scope_filter(m.Branch, False, organization_ids, city_ids)
            )
        stmt = stmt.where(m.User.id.in_(city_orders))
    if query:
        prefix = query.strip().lower()[:80]
        if prefix:
            stmt = stmt.where(func.lower(display_name).like(prefix + "%"))
    if status:
        stmt = stmt.where(m.User.status == status)
    if after:
        stmt = stmt.where(m.User.id < after)
    stmt = stmt.order_by(m.User.id.desc()).limit(limit + 1)
    rows = (await db.execute(stmt)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
            "id": str(user.id),
            "name": display_name,
            "status": user.status,
            "email": _mask_email(email),
            "email_verified": email_verified is not None,
            "phone": _mask_phone(phone),
            "phone_verified": phone_verified is not None,
            "created_at": user.created_at.isoformat(),
            "order_count": int(order_count or 0),
            "completed_order_count": int(completed_count or 0),
            "gross_purchase_value": str(gross_value or 0),
            "last_order_at": last_order.isoformat() if last_order else None,
            "value_type": "historical gross order total; refunds/discount funding not deducted",
        }
        for (
            user,
            display_name,
            email,
            email_verified,
            phone,
            phone_verified,
            order_count,
            completed_count,
            gross_value,
            last_order,
        ) in rows
    ]
    return {"items": items, "next_cursor": str(rows[-1][0].id) if has_more else None}


async def require_customer(db, user_id, *, global_access, organization_ids, city_ids):
    User = m.User
    Profile = F["identity.user_profiles"]
    Phone = F["identity.user_phone_numbers"]
    display_name = func.coalesce(
        Profile.display_name,
        func.split_part(m.Email.address, "@", 1),
        "Customer",
    )
    stmt = (
        select(
            User, display_name, m.Email.address, m.Email.verified_at, Phone.e164, Phone.verified_at
        )
        .outerjoin(Profile, Profile.user_id == User.id)
        .outerjoin(m.Email, m.Email.user_id == User.id)
        .outerjoin(Phone, Phone.user_id == User.id)
        .where(
            User.id == user_id,
            exists(
                select(m.RoleAssignment.id)
                .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
                .where(m.RoleAssignment.user_id == User.id, m.Role.name == "customer")
            ),
        )
    )
    if not global_access:
        scoped_orders = (
            select(m.Order.id)
            .join(m.MerchantOrder, m.MerchantOrder.order_id == m.Order.id)
            .join(m.Branch, m.Branch.id == m.MerchantOrder.branch_id)
            .where(
                m.Order.user_id == User.id,
                _scope_filter(m.Branch, False, organization_ids, city_ids),
            )
        )
        stmt = stmt.where(
            select(func.count()).select_from(scoped_orders.subquery()).scalar_subquery() > 0
        )
    row = (await db.execute(stmt)).first()
    if not row:
        raise BusinessError("customer_not_found", "Customer not found", 404)
    user, display, email, email_verified, phone, phone_verified = row
    display = display or (email.split("@", 1)[0] if email else "Customer")
    return {
        "id": str(user.id),
        "name": display,
        "status": user.status,
        "email": _mask_email(email),
        "email_verified": email_verified is not None,
        "phone": _mask_phone(phone),
        "phone_verified": phone_verified is not None,
        "registered_at": user.created_at.isoformat(),
    }


async def preview_segment(
    db, *, city_id, global_access, organization_ids, city_ids, logic, conditions
):
    _, _, _, orders = _customer_query(global_access, organization_ids, city_ids, city_id)
    stmt = (
        select(m.User.id)
        .outerjoin(orders, orders.c.user_id == m.User.id)
        .where(
            m.User.status != "deleted",
            orders.c.user_id.is_not(None),
            exists(
                select(m.RoleAssignment.id)
                .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
                .where(m.RoleAssignment.user_id == m.User.id, m.Role.name == "customer")
            ),
        )
    )
    predicates = []
    for condition in conditions:
        field, operator, value = condition.field, condition.op, condition.value
        if field == "status":
            if operator != "eq" or value not in {"active", "restricted", "suspended", "pending"}:
                raise BusinessError(
                    "invalid_segment_condition", "Invalid account status condition", 422
                )
            predicates.append(m.User.status == value)
        elif field == "order_count":
            if (
                operator not in {"gte", "lte"}
                or isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 100000
            ):
                raise BusinessError(
                    "invalid_segment_condition", "Invalid order count condition", 422
                )
            predicates.append(
                orders.c.order_count >= value
                if operator == "gte"
                else orders.c.order_count <= value
            )
        elif field == "gross_purchase_value":
            try:
                amount = Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                raise BusinessError(
                    "invalid_segment_condition", "Invalid purchase amount", 422
                ) from exc
            if operator not in {"gte", "lte"} or not amount.is_finite() or amount < 0:
                raise BusinessError("invalid_segment_condition", "Invalid purchase amount", 422)
            predicates.append(
                orders.c.gross_value >= amount
                if operator == "gte"
                else orders.c.gross_value <= amount
            )
        elif field == "last_order_days":
            if (
                operator != "gte"
                or isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= 3650
            ):
                raise BusinessError(
                    "invalid_segment_condition", "Dormancy days must be 1..3650", 422
                )
            predicates.append(orders.c.last_order_at <= datetime.now(UTC) - timedelta(days=value))
        elif field == "marketing_consent":
            if operator != "eq" or not isinstance(value, bool) or condition.channel is None:
                raise BusinessError(
                    "invalid_segment_condition",
                    "Consent filters require a channel and boolean value",
                    422,
                )
            consent = m.CustomerConsentEvent
            latest = (
                select(consent.enabled)
                .where(
                    consent.user_id == m.User.id,
                    consent.purpose == "marketing",
                    consent.channel == condition.channel,
                )
                .order_by(consent.created_at.desc(), consent.id.desc())
                .limit(1)
                .scalar_subquery()
            )
            predicates.append(latest == value)
        if field != "marketing_consent" and condition.channel is not None:
            raise BusinessError(
                "invalid_segment_condition", "Channel is only valid for consent rules", 422
            )
    stmt = stmt.where(and_(*predicates) if logic == "and" else or_(*predicates))
    count = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    return {
        "city_id": str(city_id),
        "logic": logic,
        "matched_count": int(count or 0),
        "definition": [condition.model_dump(mode="json") for condition in conditions],
        "count_type": "exact current database count; no personal contact details returned",
    }
