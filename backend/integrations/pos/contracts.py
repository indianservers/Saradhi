"""Small immutable POS port contracts for future provider adapters.

These protocols deliberately do not own inventory or order state. Quickbuddy remains the
system of record until an explicit, audited integration policy says otherwise.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ExternalReference:
    provider: str
    external_id: str


@dataclass(frozen=True)
class SyncCheckpoint:
    cursor: str | None
    observed_at: datetime | None


@dataclass(frozen=True)
class SyncResult:
    accepted: bool
    external_id: str | None = None
    checkpoint: SyncCheckpoint | None = None
    retryable: bool = False
    message_code: str | None = None


@runtime_checkable
class PosAdapter(Protocol):
    async def sync_catalogue(self, branch_id: str, idempotency_key: str) -> SyncResult: ...

    async def sync_prices(self, branch_id: str, idempotency_key: str) -> SyncResult: ...

    async def sync_stock(self, branch_id: str, idempotency_key: str) -> SyncResult: ...

    async def push_order(self, order: dict, idempotency_key: str) -> SyncResult: ...

    async def acknowledge_order(self, external_id: str, idempotency_key: str) -> SyncResult: ...

    async def update_preparation(
        self, external_id: str, state: str, idempotency_key: str
    ) -> SyncResult: ...

    async def cancel_order(self, external_id: str, idempotency_key: str) -> SyncResult: ...

    async def invoice_reference(
        self, external_id: str, idempotency_key: str
    ) -> ExternalReference | None: ...
