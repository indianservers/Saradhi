from datetime import timedelta
from uuid import UUID

from sqlalchemy import func, select, update

from backend.application.common import add, event, now, owned, scoped
from backend.domain.rules import BusinessError, transition
from backend.modules.dispatch.strategy import DispatchStrategy
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


async def sync_pilot_capacity(session, pilot):
    """Derive availability from authoritative active assignments after a transition."""
    active = await session.scalar(
        select(func.count())
        .select_from(m.Assignment)
        .where(
            m.Assignment.pilot_id == pilot.id,
            m.Assignment.status.in_(["offered", "accepted", "picked_up"]),
        )
    )
    if pilot.state in {"suspended", "offline", "on_break", "temporarily_unavailable"}:
        pilot.available = False
    elif active:
        pilot.state = "assigned"
        pilot.available = active < pilot.max_active_tasks
    else:
        pilot.state = "online_available"
        pilot.available = bool(pilot.verified)
    return active


async def task_context(session, task_id, lock=False):
    task = await Repository(session).require(m.DeliveryTask, task_id, lock=lock)
    unit = await Repository(session).require(m.FulfillmentUnit, task.fulfillment_unit_id)
    child = await Repository(session).require(m.MerchantOrder, unit.merchant_order_id)
    branch = await Repository(session).require(m.Branch, child.branch_id)
    return task, unit, child, branch


async def offer(session, actor, task_id, pilot_id, request_id):
    task, unit, child, branch = await task_context(session, task_id, True)
    await scoped(
        session, actor, "dispatch.write", branch.organization_id, branch.city_id, branch.id
    )
    if unit.delivery_method == "pickup":
        raise BusinessError("pickup_task", "Customer pickup does not need a pilot")
    if child.status not in {"accepted", "preparing", "ready"}:
        raise BusinessError("merchant_not_accepted", "Merchant must accept before dispatch")
    current = await session.scalar(
        select(m.Assignment)
        .where(m.Assignment.task_id == task.id, m.Assignment.status == "offered")
        .with_for_update()
    )
    if current and current.expires_at <= now():
        current.status = "expired"
        task.status = "unassigned"
        previous_pilot = await Repository(session).require(
            m.Pilot, current.pilot_id, lock=True
        )
        await sync_pilot_capacity(session, previous_pilot)
        await session.flush()
    transition("delivery", task.status, "offered")
    settings = getattr(session, "info", {}).get("settings")
    fresh_seconds = getattr(settings, "pilot_location_fresh_seconds", 90)
    active_count = (
        select(m.Assignment.pilot_id, func.count().label("active_count"))
        .where(m.Assignment.status.in_(["offered", "accepted", "picked_up"]))
        .group_by(m.Assignment.pilot_id)
        .subquery()
    )
    query = (
        select(m.Pilot, m.LatestLocation)
        .join(m.LatestLocation, m.LatestLocation.pilot_id == m.Pilot.id)
        .where(
            m.Pilot.city_id == branch.city_id,
            m.Pilot.verified.is_(True),
            m.Pilot.available.is_(True),
            m.Pilot.state.in_(["online_available", "assigned"]),
            m.LatestLocation.observed_at >= now() - timedelta(seconds=fresh_seconds),
        )
    )
    if pilot_id:
        query = query.where(m.Pilot.id == pilot_id)
    if unit.delivery_method == "merchant_delivery":
        query = query.where(
            m.Pilot.user_id.in_(
                select(m.Membership.user_id).where(
                    m.Membership.organization_id == branch.organization_id,
                    m.Membership.status == "active",
                )
            )
        )
    candidates = (await session.execute(query.with_for_update(of=m.Pilot, skip_locked=True))).all()
    if not candidates:
        raise BusinessError("no_pilot", "No eligible available pilot")
    policy = await session.scalar(
        select(F["fulfillment.dispatch_policies"])
        .where(
            F["fulfillment.dispatch_policies"].city_id == branch.city_id,
            F["fulfillment.dispatch_policies"].active.is_(True),
        )
        .order_by(F["fulfillment.dispatch_policies"].version.desc())
    )
    weights = policy.weights if policy else {"pickup_distance": 1, "workload": 5}
    active_by_pilot = dict(
        (await session.execute(select(active_count.c.pilot_id, active_count.c.active_count))).all()
    )
    strategy = DispatchStrategy()
    scored = []
    for candidate, location in candidates:
        active = active_by_pilot.get(candidate.id, 0)
        if active >= candidate.max_active_tasks or candidate.state == "suspended":
            continue
        scored.append((strategy.score(candidate.id, location, branch, active, weights), candidate))
    if not scored:
        raise BusinessError("no_pilot", "No pilot has fresh location and free capacity")
    _, pilot = min(scored, key=lambda item: (item[0].score, str(item[0].pilot_id)))
    assignment = await add(
        session,
        m.Assignment,
        task_id=task.id,
        pilot_id=pilot.id,
        expires_at=now() + timedelta(seconds=60),
    )
    task.status, task.version = "offered", task.version + 1
    await sync_pilot_capacity(session, pilot)
    if active_by_pilot.get(pilot.id, 0) == 0:
        pilot.state = "offer_pending"
        pilot.available = False
    await add(
        session,
        F["fulfillment.dispatch_events"],
        task_id=task.id,
        event_type="offer_created",
        actor_id=UUID(actor.subject),
        strategy=f"{strategy.name};policy={policy.version if policy else 1}",
    )
    await event(
        session,
        "pilot.offered",
        task.id,
        request_id,
        assignment_id=assignment.id,
        pilot_id=pilot.id,
        order_id=child.order_id,
        organization_id=branch.organization_id,
        city_id=branch.city_id,
    )
    return assignment


async def accept(session, actor, assignment_id, request_id):
    # All task operations lock task then assignment: avoids accept/expire lock inversion.
    candidate = await Repository(session).require(m.Assignment, assignment_id)
    task, unit, child, branch = await task_context(session, candidate.task_id, True)
    assignment = await session.scalar(
        select(m.Assignment).where(m.Assignment.id == assignment_id).with_for_update()
    )
    pilot = await Repository(session).require(m.Pilot, assignment.pilot_id, lock=True)
    owned(actor, pilot.user_id)
    if not pilot.verified:
        raise BusinessError("pilot_unverified", "Pilot verification has been revoked", 403)
    if assignment.status == "accepted" and task.status == "assigned":
        return task
    if assignment.status != "offered" or assignment.expires_at <= now():
        raise BusinessError("offer_expired", "Offer is unavailable or expired")
    if pilot.state not in {"offer_pending", "assigned"}:
        raise BusinessError(
            "pilot_unavailable",
            "Pilot must be online and available to accept this offer",
            409,
        )
    active_count = await session.scalar(
        select(func.count())
        .select_from(m.Assignment)
        .where(
            m.Assignment.pilot_id == pilot.id,
            m.Assignment.status.in_(["offered", "accepted", "picked_up"]),
        )
    )
    if int(active_count or 0) > pilot.max_active_tasks:
        raise BusinessError("pilot_capacity", "Pilot task capacity has been reached", 409)
    transition("delivery", task.status, "assigned")
    assignment.status = "accepted"
    task.status, task.version = "assigned", task.version + 1
    await sync_pilot_capacity(session, pilot)
    await add(
        session,
        F["fulfillment.dispatch_events"],
        task_id=task.id,
        event_type="offer_accepted",
        actor_id=UUID(actor.subject),
        strategy="pilot_acceptance",
    )
    await event(
        session,
        "pilot.assigned",
        task.id,
        request_id,
        assignment_id=assignment.id,
        pilot_id=pilot.id,
        order_id=child.order_id,
        organization_id=branch.organization_id,
        city_id=branch.city_id,
    )
    return task


async def reject_offer(session, actor, assignment_id, request_id):
    assignment = await Repository(session).require(m.Assignment, assignment_id)
    task, unit, child, branch = await task_context(session, assignment.task_id, True)
    assignment = await Repository(session).require(m.Assignment, assignment_id, lock=True)
    pilot = await Repository(session).require(m.Pilot, assignment.pilot_id, lock=True)
    owned(actor, pilot.user_id)
    if assignment.status != "offered" or assignment.expires_at <= now():
        raise BusinessError("offer_expired", "Offer is unavailable or expired")
    assignment.status = "rejected"
    task.status, task.version = "unassigned", task.version + 1
    await sync_pilot_capacity(session, pilot)
    await add(
        session,
        F["fulfillment.assignment_responses"],
        assignment_id=assignment.id,
        response="rejected",
        responded_at=now(),
    )
    await add(
        session,
        F["fulfillment.dispatch_events"],
        task_id=task.id,
        event_type="offer_rejected",
        actor_id=UUID(actor.subject),
        strategy="pilot_response",
    )
    await event(
        session,
        "pilot.offer_rejected",
        task.id,
        request_id,
        assignment_id=assignment.id,
        pilot_id=pilot.id,
        order_id=child.order_id,
        organization_id=branch.organization_id,
        city_id=branch.city_id,
    )
    return task


async def expire_offers(session, limit=100):
    """Worker-safe bounded expiry. Task locks and the partial unique index arbitrate replicas."""
    candidates = (
        await session.execute(
            select(m.DeliveryTask, m.Assignment)
            .join(m.Assignment, m.Assignment.task_id == m.DeliveryTask.id)
            .where(m.Assignment.status == "offered", m.Assignment.expires_at <= now())
            .order_by(m.Assignment.expires_at, m.DeliveryTask.id)
            .with_for_update(of=m.DeliveryTask, skip_locked=True)
            .limit(limit)
        )
    ).all()
    expired = 0
    for task, candidate in candidates:
        assignment = await session.scalar(
            select(m.Assignment)
            .where(m.Assignment.id == candidate.id, m.Assignment.status == "offered")
            .with_for_update()
        )
        if not assignment or assignment.expires_at > now():
            continue
        task, unit, child, branch = await task_context(session, task.id)
        assignment.status = "expired"
        if task.status == "offered":
            task.status, task.version = "unassigned", task.version + 1
        pilot = await Repository(session).require(m.Pilot, assignment.pilot_id, lock=True)
        await sync_pilot_capacity(session, pilot)
        await event(
            session,
            "pilot.offer_expired",
            task.id,
            "dispatch-expiry-worker",
            pilot_id=pilot.id,
            order_id=child.order_id,
            organization_id=branch.organization_id,
            city_id=branch.city_id,
        )
        expired += 1
    return expired


async def progress(session, actor, task_id, target, expected_version, request_id):
    task, unit, child, branch = await task_context(session, task_id, True)
    if task.version != expected_version:
        raise BusinessError("version_conflict", "Expected task version does not match")
    assignment = await session.scalar(
        select(m.Assignment)
        .where(m.Assignment.task_id == task.id, m.Assignment.status.in_(["accepted", "picked_up"]))
        .with_for_update()
    )
    if not assignment:
        raise BusinessError("unassigned", "No active pilot assignment")
    pilot = await Repository(session).require(m.Pilot, assignment.pilot_id)
    owned(actor, pilot.user_id)
    transition("delivery", task.status, target)
    if target == "picked_up" and child.status != "ready":
        raise BusinessError("not_ready", "Merchant preparation must be ready before pickup")
    if target == "delivered":
        raise BusinessError(
            "proof_required", "Use the recipient acknowledgment endpoint to confirm delivery"
        )
    task.status, task.version = target, task.version + 1
    assignment.status = "picked_up" if target == "picked_up" else "failed"
    if target != "picked_up":
        await sync_pilot_capacity(session, pilot)
    model = (
        F["fulfillment.pickup_confirmations"]
        if target == "picked_up"
        else F["fulfillment.delivery_attempts"]
    )
    values = {"task_id": task.id, "pilot_id": pilot.id}
    values.update({"confirmed_at": now()} if target == "picked_up" else {"outcome": "failed"})
    await add(session, model, **values)
    await event(
        session,
        "order.picked_up" if target == "picked_up" else "delivery.failed",
        task.id,
        request_id,
        order_id=child.order_id,
        pilot_id=pilot.id,
        organization_id=branch.organization_id,
        city_id=branch.city_id,
    )
    return task


async def recipient_complete(session, actor, task_id, expected_version, request_id):
    task, unit, child, branch = await task_context(session, task_id, True)
    order = await Repository(session).require(m.Order, child.order_id, lock=True)
    owned(actor, order.user_id)
    if task.version != expected_version:
        raise BusinessError("version_conflict", "Expected task version does not match")
    if unit.delivery_method == "pickup":
        if child.status != "ready" or task.status != "unassigned":
            raise BusinessError("not_ready", "Pickup is not ready")
    else:
        transition("delivery", task.status, "delivered")
        assignment = await session.scalar(
            select(m.Assignment)
            .where(m.Assignment.task_id == task.id, m.Assignment.status == "picked_up")
            .with_for_update()
        )
        if not assignment:
            raise BusinessError("assignment_missing", "No picked-up assignment")
        assignment.status = "completed"
        pilot = await Repository(session).require(m.Pilot, assignment.pilot_id, lock=True)
        await sync_pilot_capacity(session, pilot)
        await add(
            session,
            F["fulfillment.delivery_confirmations"],
            task_id=task.id,
            pilot_id=assignment.pilot_id,
            confirmed_at=now(),
            mode="recipient_acknowledgment",
        )
    await add(
        session,
        F["fulfillment.proof_of_delivery"],
        task_id=task.id,
        mode="recipient_acknowledgment",
        acknowledged_by=UUID(actor.subject),
        expires_at=now() + timedelta(days=30),
    )
    task.status, task.version, unit.status = "delivered", task.version + 1, "delivered"
    await session.execute(
        update(m.Window).where(m.Window.id == unit.window_id).values(reserved=m.Window.reserved - 1)
    )
    other_units = await session.scalar(
        select(m.FulfillmentUnit.id).where(
            m.FulfillmentUnit.merchant_order_id == child.id,
            m.FulfillmentUnit.id != unit.id,
            m.FulfillmentUnit.status.not_in(["delivered", "cancelled"]),
        )
    )
    if not other_units:
        child.status, child.version = "fulfilled", child.version + 1
        await add(
            session,
            m.OrderHistory,
            order_id=order.id,
            merchant_order_id=child.id,
            previous="ready",
            current="fulfilled",
            actor_id=UUID(actor.subject),
        )
    await session.flush()
    outstanding = await session.scalar(
        select(m.MerchantOrder.id).where(
            m.MerchantOrder.order_id == order.id,
            m.MerchantOrder.status.not_in(["fulfilled", "rejected", "cancelled"]),
        )
    )
    if not outstanding:
        order.status, order.version = "completed", order.version + 1
        await add(
            session,
            m.OrderHistory,
            order_id=order.id,
            previous="confirmed",
            current="completed",
            actor_id=UUID(actor.subject),
        )
    await event(
        session,
        "order.delivered",
        task.id,
        request_id,
        order_id=order.id,
        organization_id=branch.organization_id,
        city_id=branch.city_id,
    )
    return task
