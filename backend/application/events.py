"""PostgreSQL outbox relay with leased claims and at-least-once publication."""

import random
from datetime import timedelta
from typing import Protocol
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.application.common import now
from backend.persistence import models as m


class EventPublisher(Protocol):
    async def publish(
        self, event_id: str, aggregate_id: str, event_type: str, payload_version: int, payload: dict
    ) -> None: ...


async def _claim_batch(sessions: async_sessionmaker, limit: int, lease_seconds: int):
    claimed = []
    instant = now()
    async with sessions.begin() as session:
        events = (
            await session.scalars(
                select(m.Outbox)
                .where(
                    m.Outbox.delivered_at.is_(None),
                    m.Outbox.dead_lettered_at.is_(None),
                    m.Outbox.available_at <= instant,
                    or_(m.Outbox.claim_expires_at.is_(None), m.Outbox.claim_expires_at <= instant),
                )
                .order_by(m.Outbox.available_at, m.Outbox.id)
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
        ).all()
        for event in events:
            token = uuid4()
            event.claim_token = token
            event.claim_expires_at = instant + timedelta(seconds=lease_seconds)
            claimed.append(
                (
                    event.id,
                    token,
                    event.aggregate_id,
                    event.event_type,
                    event.payload_version,
                    event.payload,
                )
            )
    # session.begin committed leases before external I/O begins.
    return claimed


async def relay_batch(
    sessions: async_sessionmaker,
    publisher: EventPublisher,
    limit: int = 50,
    lease_seconds: int = 120,
) -> int:
    """Claim durably, publish without a transaction, then acknowledge or schedule retry.

    Delivery is at least once: a process may publish successfully and crash before marking
    delivered. Every downstream consumer must deduplicate by event_id. Broker request
    timeouts must be shorter than the claim lease; expired leases permit crash recovery.
    """
    if not 1 <= limit <= 500 or not 10 <= lease_seconds <= 3600:
        raise ValueError("Outbox batch and lease bounds are invalid")
    events = await _claim_batch(sessions, limit, lease_seconds)
    for event_id, token, aggregate_id, event_type, version, payload in events:
        try:
            await publisher.publish(str(event_id), str(aggregate_id), event_type, version, payload)
        except Exception:
            instant = now()
            async with sessions.begin() as session:
                event = await session.scalar(
                    select(m.Outbox)
                    .where(m.Outbox.id == event_id, m.Outbox.claim_token == token)
                    .with_for_update()
                )
                if event is None or event.delivered_at is not None:
                    continue
                event.attempts += 1
                event.claim_token = event.claim_expires_at = None
                if event.attempts >= 8:
                    event.dead_lettered_at = instant
                else:
                    event.available_at = instant + timedelta(
                        seconds=min(3600, 2**event.attempts) + random.random()
                    )
            # Deliberately store no exception text: provider errors can contain secrets/PII.
        else:
            async with sessions.begin() as session:
                await session.execute(
                    update(m.Outbox)
                    .where(
                        m.Outbox.id == event_id,
                        m.Outbox.claim_token == token,
                        m.Outbox.delivered_at.is_(None),
                    )
                    .values(delivered_at=now(), claim_token=None, claim_expires_at=None)
                )
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
