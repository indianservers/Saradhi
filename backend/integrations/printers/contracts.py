"""Validated ticket contracts independent of ESC/POS, Bluetooth, or network hardware."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class TicketLine:
    quantity: str
    name: str
    notes: str = ""


@dataclass(frozen=True)
class KitchenTicket:
    ticket_id: str
    order_number: str
    station: str
    lines: tuple[TicketLine, ...]
    printed_at: datetime
    reprint_reason: str | None = None


@dataclass(frozen=True)
class PrintResult:
    accepted: bool
    duplicate: bool = False
    device_reference: str | None = None


@runtime_checkable
class PrinterAdapter(Protocol):
    async def print_ticket(self, ticket: KitchenTicket, idempotency_key: str) -> PrintResult: ...
