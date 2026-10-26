"""Bounded durable maintenance units; run from worker jobs, never web lifespan timers."""

from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from backend.application.commerce import release_reservation
from backend.application.common import add, now, owned
from backend.domain.rules import BusinessError
from backend.domain.scheduling import occurrences
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def expire_reservations(session, limit=100, reservation_id=None):
    scope = [m.Reservation.id == reservation_id] if reservation_id is not None else []
    rows = (
        await session.scalars(
            select(m.Reservation)
            .where(m.Reservation.status == "reserved", m.Reservation.expires_at <= now())
            .where(*scope)
            .order_by(m.Reservation.stock_id, m.Reservation.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
    ).all()
    for reservation in rows:
        await release_reservation(session, reservation, None, "reservation-expiry")
    return len(rows)


async def materialize_occurrences(session, plan_id, instants):
    plan = await session.get(F["fulfillment.recurring_order_plans"], plan_id)
    if not plan or not plan.active or plan.status != "active":
        raise BusinessError("inactive_plan", "Recurring plan is unavailable")
    model = F["fulfillment.scheduled_order_occurrences"]
    created = []
    for instant in instants:
        if instant.tzinfo is None:
            raise BusinessError(
                "ambiguous_schedule", "Occurrences require offset-aware instants", 422
            )
        row = await session.scalar(
            insert(model)
            .values(
                plan_id=plan.id,
                scheduled_at=instant,
                status="awaiting_revalidation",
                revalidation_reason="merchant_stock_price_payment_required",
            )
            .on_conflict_do_nothing(index_elements=["plan_id", "scheduled_at"])
            .returning(model.id)
        )
        if row:
            created.append(row)
            await session.execute(
                insert(F["fulfillment.scheduling_job_records"])
                .values(occurrence_id=row, attempts=0, available_at=now(), locked_until=None)
                .on_conflict_do_nothing(index_elements=["occurrence_id"])
            )
    # No payment agreement -> still persisted for review, never an automatic charge.
    return created


async def expand_recurrence(session, plan_id, start, end):
    Plan, Rule, ExceptionModel = (
        F["fulfillment." + name]
        for name in ["recurring_order_plans", "recurring_order_rules", "recurrence_exceptions"]
    )
    plan = await session.scalar(select(Plan).where(Plan.id == plan_id).with_for_update())
    if not plan or not plan.active or plan.status != "active":
        raise BusinessError("inactive_plan", "Recurring plan is unavailable")
    rules = (await session.scalars(select(Rule).where(Rule.plan_id == plan.id))).all()
    exceptions = set(
        (
            await session.scalars(
                select(ExceptionModel.local_date).where(
                    ExceptionModel.plan_id == plan.id, ExceptionModel.skip.is_(True)
                )
            )
        ).all()
    )
    instants = set()
    for rule in rules:
        if rule.end_date and rule.end_date < start:
            continue
        instants.update(
            occurrences(
                rule.start_date,
                start,
                min(end, rule.end_date) if rule.end_date else end,
                rule.local_time,
                plan.timezone,
                rule.frequency,
                rule.interval,
                exceptions,
            )
        )
    instants = {instant for instant in instants if instant > now()}
    return await materialize_occurrences(session, plan.id, sorted(instants))


async def redeem_coupon(session, actor, coupon_id, order_id, branch_id, amount):
    order = await session.scalar(select(m.Order).where(m.Order.id == order_id).with_for_update())
    if not order:
        raise BusinessError("not_found", "Order not found", 404)
    owned(actor, order.user_id)
    coupon_model, redemption = F["engagement.coupons"], F["engagement.coupon_redemptions"]
    coupon = await session.scalar(
        select(coupon_model).where(coupon_model.id == coupon_id).with_for_update()
    )
    if not coupon:
        raise BusinessError("not_found", "Coupon not found", 404)
    campaign = await session.get(F["engagement.promotional_campaigns"], coupon.campaign_id)
    if campaign.starts_at > now() or campaign.ends_at <= now():
        raise BusinessError("coupon_expired", "Campaign is outside its active period")
    child = await session.scalar(
        select(m.MerchantOrder).where(
            m.MerchantOrder.order_id == order_id, m.MerchantOrder.branch_id == branch_id
        )
    )
    branch = await session.get(m.Branch, branch_id)
    if not child or not branch or branch.organization_id != campaign.organization_id:
        raise BusinessError("coupon_scope", "Coupon does not apply to this merchant order", 403)
    prior = await session.scalar(
        select(redemption).where(
            redemption.coupon_id == coupon_id,
            redemption.order_id == order_id,
            redemption.branch_id == branch_id,
        )
    )
    if prior:
        if prior.amount != amount:
            raise BusinessError("idempotency_conflict", "Coupon amount changed")
        return prior
    existing = (
        await session.scalars(select(redemption).where(redemption.order_id == order_id))
    ).all()
    if existing:
        other_coupons = (
            await session.scalars(
                select(coupon_model).where(coupon_model.id.in_([v.coupon_id for v in existing]))
            )
        ).all()
        if not coupon.stackable or any(not value.stackable for value in other_coupons):
            raise BusinessError("coupon_stacking", "Coupon policy disallows stacking")
    user_count = await session.scalar(
        select(func.count())
        .select_from(redemption)
        .where(redemption.coupon_id == coupon_id, redemption.user_id == UUID(actor.subject))
    )
    merchant_count = await session.scalar(
        select(func.count())
        .select_from(redemption)
        .where(redemption.coupon_id == coupon_id, redemption.branch_id == branch_id)
    )
    if (
        coupon.redeemed >= coupon.total_limit
        or user_count >= coupon.per_user_limit
        or merchant_count >= coupon.per_merchant_limit
    ):
        raise BusinessError("coupon_exhausted", "Coupon redemption limit reached")
    if amount <= 0 or amount > child.total:
        raise BusinessError("coupon_amount", "Invalid coupon allocation", 422)
    # This internal operation records entitlement consumption only; no endpoint silently
    # changes an already confirmed order. Future quote pricing must call it atomically.
    coupon.redeemed += 1
    return await add(
        session,
        redemption,
        coupon_id=coupon.id,
        user_id=UUID(actor.subject),
        order_id=order.id,
        branch_id=branch_id,
        amount=amount,
    )


async def prune_ephemeral(session, limit=1000):
    counts = {}
    policies = [
        (F["fulfillment.pilot_location_events"], "expires_at", now()),
        (F["fulfillment.proof_of_delivery"], "expires_at", now()),
        (m.RateBucket, "window_start", now() - timedelta(days=1)),
    ]
    for model, column, cutoff in policies:
        ids = (
            select(model.id).where(getattr(model, column) < cutoff).order_by(model.id).limit(limit)
        )
        result = await session.execute(delete(model).where(model.id.in_(ids)))
        counts[model.__name__] = result.rowcount
    return counts
