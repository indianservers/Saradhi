"""PostgreSQL-backed outbox relay with at-least-once external delivery."""

import random
from datetime import timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.application.common import now
from backend.persistence import models as m


class EventPublisher(Protocol):
    async def publish(
        self, event_id: str, event_type: str, payload_version: int, payload: dict
    ) -> None: ...


async def relay_batch(session, publisher: EventPublisher, limit=50):
    events = (
        await session.scalars(
            select(m.Outbox)
            .where(
                m.Outbox.delivered_at.is_(None),
                m.Outbox.dead_lettered_at.is_(None),
                m.Outbox.available_at <= now(),
            )
            .order_by(m.Outbox.created_at, m.Outbox.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
    ).all()
    for event in events:
        try:
            await publisher.publish(
                str(event.id), event.event_type, event.payload_version, event.payload
            )
        except Exception:
            event.attempts += 1
            if event.attempts >= 8:
                event.dead_lettered_at = now()
            else:
                event.available_at = now() + timedelta(
                    seconds=min(3600, 2**event.attempts) + random.random()
                )
        else:
            event.delivered_at = now()
    return len(events)


async def consume(session, consumer_name, event_id, handler, payload):
    # Inbox marker and handler effects share this caller-owned transaction. A failed
    # handler rolls back both. External effects require their own idempotency contract.
    marker = await session.scalar(
        insert(m.Inbox)
        .values(consumer=consumer_name, event_id=event_id)
        .on_conflict_do_nothing(index_elements=["consumer", "event_id"])
        .returning(m.Inbox.id)
    )
    if marker is None:
        return False
    await handler(session, payload)
    return True
