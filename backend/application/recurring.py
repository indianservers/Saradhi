"""Customer-owned recurring schedules with idempotent review-only occurrence creation."""

from datetime import date, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.application import commerce, maintenance
from backend.application.common import add, now, owned
from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


async def create_plan(session, actor, body):
    if body.start_date < now().astimezone(ZoneInfo(body.timezone)).date():
        raise BusinessError(
            "schedule_start_in_past", "Recurring schedule must start today or later", 422
        )
    cart = await commerce.cart_context(session, actor, body.cart_id)
    items = (await session.scalars(select(m.CartItem).where(m.CartItem.cart_id == cart.id))).all()
    if not items:
        raise BusinessError("empty_recurring_cart", "Add items before scheduling a recurring order")
    template = []
    for item in items:
        address_id = None
        if item.address_id:
            address = await Repository(session).require(m.Address, item.address_id)
            owned(actor, address.user_id)
            address_id = str(address.id)
        variant = await Repository(session).require(m.Variant, item.variant_id)
        product = await Repository(session).require(m.Product, variant.product_id)
        category = await Repository(session).require(m.Category, product.category_id)
        if category.regulated or product.variable_weight:
            raise BusinessError(
                "recurrence_not_supported",
                "Regulated and variable-weight products cannot be scheduled for recurring checkout",
                422,
            )
        template.append(
            {
                "branch_id": str(item.branch_id),
                "variant_id": str(item.variant_id),
                "quantity": str(item.quantity),
                "delivery_method": item.delivery_method,
                "address_id": address_id,
                "category_id": str(product.category_id),
            }
        )
    Plan = F["fulfillment.recurring_order_plans"]
    Rule = F["fulfillment.recurring_order_rules"]
    plan = await add(
        session,
        Plan,
        user_id=UUID(actor.subject),
        cart_template={"items": template},
        timezone=body.timezone,
        payment_agreement_reference=None,
        active=True,
        status="active",
    )
    await add(
        session,
        Rule,
        plan_id=plan.id,
        frequency=body.frequency,
        interval=body.interval,
        local_time=body.local_time,
        start_date=body.start_date,
        end_date=body.end_date,
    )
    return plan


async def owned_plan(session, actor, plan_id, lock=False):
    plan = await Repository(session).require(
        F["fulfillment.recurring_order_plans"], plan_id, lock=lock
    )
    owned(actor, plan.user_id)
    return plan


async def plan_view(session, plan):
    Rule = F["fulfillment.recurring_order_rules"]
    rules = (await session.scalars(select(Rule).where(Rule.plan_id == plan.id))).all()
    return {
        "id": plan.id,
        "status": plan.status,
        "active": plan.active,
        "timezone": plan.timezone,
        "item_count": len(plan.cart_template.get("items", [])),
        "payment_authorized": bool(plan.payment_agreement_reference),
        "rules": [
            {
                "frequency": rule.frequency,
                "interval": rule.interval,
                "local_time": rule.local_time,
                "start_date": rule.start_date,
                "end_date": rule.end_date,
            }
            for rule in rules
        ],
        "execution_policy": "review_required_no_automatic_charge_or_order",
    }


async def set_status(session, actor, plan_id, status):
    plan = await owned_plan(session, actor, plan_id, lock=True)
    if plan.status == "cancelled" and status != "cancelled":
        raise BusinessError("plan_cancelled", "Cancelled recurring plans cannot be resumed", 409)
    if status == "cancelled":
        plan.active = False
        plan.status = "cancelled"
        Occurrence = F["fulfillment.scheduled_order_occurrences"]
        pending = (
            await session.scalars(
                select(Occurrence)
                .where(
                    Occurrence.plan_id == plan.id,
                    Occurrence.order_id.is_(None),
                    Occurrence.status == "awaiting_revalidation",
                )
                .with_for_update()
            )
        ).all()
        for occurrence in pending:
            occurrence.status = "cancelled"
            occurrence.revalidation_reason = "plan_cancelled"
    elif status in {"active", "paused"}:
        plan.active = status == "active"
        plan.status = status
    else:
        raise BusinessError("invalid_plan_status", "Unsupported recurring plan state", 422)
    return plan


async def skip_local_date(session, actor, plan_id, local_date: date):
    plan = await owned_plan(session, actor, plan_id, lock=True)
    if plan.status == "cancelled":
        raise BusinessError("plan_cancelled", "Cancelled recurring plans cannot be changed", 409)
    today = now().astimezone(ZoneInfo(plan.timezone)).date()
    if local_date < today:
        raise BusinessError("occurrence_in_past", "Past recurring dates cannot be skipped", 422)
    ExceptionModel = F["fulfillment.recurrence_exceptions"]
    await session.execute(
        insert(ExceptionModel)
        .values(plan_id=plan.id, local_date=local_date, skip=True)
        .on_conflict_do_update(index_elements=["plan_id", "local_date"], set_={"skip": True})
    )
    Occurrence = F["fulfillment.scheduled_order_occurrences"]
    scheduled = (
        await session.scalars(
            select(Occurrence)
            .where(Occurrence.plan_id == plan.id, Occurrence.order_id.is_(None))
            .with_for_update()
        )
    ).all()
    marked = 0
    for occurrence in scheduled:
        local = occurrence.scheduled_at.astimezone(ZoneInfo(plan.timezone))
        if local.date() == local_date and occurrence.status == "awaiting_revalidation":
            occurrence.status = "skipped"
            occurrence.revalidation_reason = "customer_skipped"
            marked += 1
    return {
        "plan_id": plan.id,
        "local_date": local_date,
        "status": "skipped",
        "occurrences_updated": marked,
    }


async def expand_active_plans(session, limit=100, horizon_days=14):
    Plan = F["fulfillment.recurring_order_plans"]
    plans = (
        await session.scalars(
            select(Plan)
            .where(Plan.active.is_(True), Plan.status == "active")
            .order_by(Plan.updated_at, Plan.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
    ).all()
    created = 0
    failed = []
    for plan in plans:
        local_start = now().astimezone(ZoneInfo(plan.timezone)).date()
        try:
            rows = await maintenance.expand_recurrence(
                session, plan.id, local_start, local_start + timedelta(days=horizon_days)
            )
        except BusinessError as exc:
            failed.append({"plan_id": str(plan.id), "error": exc.code})
            plan.updated_at = now()
            continue
        created += len(rows)
        plan.updated_at = now()
    return {
        "plans_scanned": len(plans),
        "occurrences_created": created,
        "schedule_errors": failed,
    }
