"""First-expiry-first-out reservations with row locks and allocation traceability."""

from datetime import date

from sqlalchemy import select

from backend.application.common import add, now
from backend.domain.rules import BusinessError
from backend.persistence.foundations import FOUNDATION_MODELS as F


async def allocate(session, reservation, delivery_date: date):
    Batch, Expiry, Allocation = (
        F["inventory." + name]
        for name in ["stock_batches", "expiry_dates", "batch_reservation_allocations"]
    )
    rows = (
        await session.execute(
            select(Batch, Expiry.expires_on)
            .outerjoin(Expiry, Expiry.batch_id == Batch.id)
            .where(Batch.stock_id == reservation.stock_id)
            .order_by(Expiry.expires_on.asc().nulls_last(), Batch.received_at, Batch.id)
            .with_for_update(of=Batch)
        )
    ).all()
    if not rows:
        return
    remaining = reservation.quantity
    for batch, expires in rows:
        if expires is not None and expires < delivery_date:
            continue
        take = min(remaining, batch.quantity - batch.reserved)
        if take <= 0:
            continue
        batch.reserved += take
        await add(
            session,
            Allocation,
            reservation_id=reservation.id,
            batch_id=batch.id,
            quantity=take,
            status="reserved",
        )
        remaining -= take
        if remaining == 0:
            break
    if remaining > 0:
        raise BusinessError(
            "batch_stock_unavailable", "Insufficient unexpired stock for the delivery date"
        )


async def finish(session, reservation, consume=False, at_date=None):
    Allocation, Batch, Expiry = (
        F["inventory." + name]
        for name in ["batch_reservation_allocations", "stock_batches", "expiry_dates"]
    )
    rows = (
        await session.scalars(
            select(Allocation)
            .where(Allocation.reservation_id == reservation.id)
            .order_by(Allocation.batch_id)
            .with_for_update()
        )
    ).all()
    for allocation in rows:
        if allocation.status != "reserved":
            continue
        batch = await session.scalar(
            select(Batch).where(Batch.id == allocation.batch_id).with_for_update()
        )
        if consume:
            expires = await session.scalar(
                select(Expiry.expires_on).where(Expiry.batch_id == batch.id)
            )
            if expires is not None and expires < (at_date or now().date()):
                raise BusinessError(
                    "expired_batch", "Reserved batch has expired; do not prepare or deliver"
                )
            batch.quantity -= allocation.quantity
        batch.reserved -= allocation.quantity
        allocation.status = "consumed" if consume else "released"
