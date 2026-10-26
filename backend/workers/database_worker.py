"""Database-backed reaper and in-app notification handoff.

Due state, idempotency and effects are persisted. No payment/order workflow is scheduled
in process memory. External SMS/email/broker delivery remains unconfigured and is not claimed.
"""

import argparse
import asyncio
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.application.common import add, now
from backend.application.events import consume
from backend.application.maintenance import expire_reservations, prune_ephemeral
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.shared.database import create_database
from backend.shared.settings import get_settings


async def internal_notifications(session, limit=50):
    rows = (
        await session.scalars(
            select(m.Outbox)
            .where(
                m.Outbox.event_type == "order.created",
                m.Outbox.delivered_at.is_(None),
                m.Outbox.dead_lettered_at.is_(None),
                m.Outbox.available_at <= now(),
            )
            .order_by(m.Outbox.created_at, m.Outbox.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
    ).all()
    for event in rows:
        order = await session.get(m.Order, event.aggregate_id)
        if not order:
            continue

        async def handle(db, payload, event=event, order=order):
            await add(
                db,
                F["operations.notification_jobs"],
                user_id=order.user_id,
                event_id=event.id,
                channel="in_app",
                status="available",
                available_at=now(),
            )

        await consume(session, "in_app_notifications.v1", event.id, handle, event.payload)
        event.delivered_at = now()  # Means internal handoff ONLY, not SMS/push delivery.
    return len(rows)


async def tick(sessions):
    async with sessions.begin() as db:
        expired = await expire_reservations(db)
    async with sessions.begin() as db:
        notifications = await internal_notifications(db)
    async with sessions.begin() as db:
        pruned = await prune_ephemeral(db)
    return {"expired_reservations": expired, "in_app_handoffs": notifications, "pruned": pruned}


async def main(once):
    settings = get_settings()
    if "REPLACE_ME" in settings.database_url.get_secret_value():
        raise SystemExit("Authorized database configuration is required")
    engine = create_database(settings)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    try:
        while True:
            print(json.dumps(await tick(sessions)))
            if once:
                break
            await asyncio.sleep(5)  # Poll interval only; due state lives in PostgreSQL.
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    asyncio.run(main(parser.parse_args().once))
