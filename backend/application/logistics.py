from datetime import timedelta
from uuid import UUID

from sqlalchemy import select, update

from backend.application.common import add, event, now, owned, scoped
from backend.domain.rules import BusinessError, transition
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


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
        await session.flush()
    transition("delivery", task.status, "offered")
    # Stable UUID ordering is a deterministic replacement point for future dispatch strategies.
    query = select(m.Pilot).where(
        m.Pilot.city_id == branch.city_id, m.Pilot.verified.is_(True), m.Pilot.available.is_(True)
    )
    if pilot_id:
        query = query.where(m.Pilot.id == pilot_id)
    pilot = await session.scalar(
        query.order_by(m.Pilot.id).with_for_update(skip_locked=True).limit(1)
    )
    if not pilot:
        raise BusinessError("no_pilot", "No eligible available pilot")
    assignment = await add(
        session,
        m.Assignment,
        task_id=task.id,
        pilot_id=pilot.id,
        expires_at=now() + timedelta(seconds=60),
    )
    task.status, task.version = "offered", task.version + 1
    await event(session, "pilot.offered", task.id, request_id, pilot_id=pilot.id)
    return assignment


async def accept(session, actor, assignment_id, request_id):
    # All task operations lock task then assignment: avoids accept/expire lock inversion.
    candidate = await Repository(session).require(m.Assignment, assignment_id)
    task, unit, child, branch = await task_context(session, candidate.task_id, True)
    assignment = await session.scalar(
        select(m.Assignment).where(m.Assignment.id == assignment_id).with_for_update()
    )
    pilot = await Repository(session).require(m.Pilot, assignment.pilot_id)
    owned(actor, pilot.user_id)
    if assignment.status == "accepted" and task.status == "assigned":
        return task
    if assignment.status != "offered" or assignment.expires_at <= now():
        raise BusinessError("offer_expired", "Offer is unavailable or expired")
    transition("delivery", task.status, "assigned")
    assignment.status = "accepted"
    task.status, task.version = "assigned", task.version + 1
    await event(session, "pilot.assigned", task.id, request_id, pilot_id=pilot.id)
    return task


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
    await event(session, "order.delivered", task.id, request_id, order_id=order.id)
    return task
