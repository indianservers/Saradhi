"""Contracts only: no claim of reliable delivery or storage implementations."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    id: UUID
    name: str
    version: int
    occurred_at: datetime
    aggregate_id: str
    correlation_id: str
    payload: Mapping[str, object]


class TransactionalOutbox(Protocol):
    async def append(self, event: DomainEvent, transaction: object) -> None: ...


class IdempotentConsumer(Protocol):
    async def consume(self, event: DomainEvent) -> None:
        """Commit deduplication marker and local effects in the same DB transaction."""
        ...


class RetryPolicy(Protocol):
    def delay_seconds(self, attempt: int) -> float | None:
        """None sends to durable dead-letter storage; otherwise bounded exponential jitter."""
        ...


class ObjectStorage(Protocol):
    async def signed_upload_url(self, key: str, content_type: str) -> str: ...


class AuditSink(Protocol):
    async def record(self, actor: str, action: str, resource: str, request_id: str) -> None: ...
