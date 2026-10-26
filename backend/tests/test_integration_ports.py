"""Local adapter-contract smoke tests; these do not simulate a real POS or printer."""

import asyncio
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from backend.integrations.pos.contracts import (
    ExternalReference,
    PosAdapter,
    SyncResult,
)
from backend.integrations.printers.contracts import (
    KitchenTicket,
    PrinterAdapter,
    PrintResult,
    TicketLine,
)


class _LocalPosFixture:
    async def sync_catalogue(self, branch_id, idempotency_key):
        return SyncResult(True, external_id=f"catalogue-{branch_id}")

    async def sync_prices(self, branch_id, idempotency_key):
        return SyncResult(True)

    async def sync_stock(self, branch_id, idempotency_key):
        return SyncResult(True)

    async def push_order(self, order, idempotency_key):
        return SyncResult(True, external_id=f"order-{idempotency_key}")

    async def acknowledge_order(self, external_id, idempotency_key):
        return SyncResult(True, external_id=external_id)

    async def update_preparation(self, external_id, state, idempotency_key):
        return SyncResult(True, external_id=external_id)

    async def cancel_order(self, external_id, idempotency_key):
        return SyncResult(True, external_id=external_id)

    async def invoice_reference(self, external_id, idempotency_key):
        return ExternalReference("local-fixture", external_id)


class _LocalPrinterFixture:
    def __init__(self):
        self.keys = set()

    async def print_ticket(self, ticket, idempotency_key):
        duplicate = idempotency_key in self.keys
        self.keys.add(idempotency_key)
        return PrintResult(accepted=not duplicate, duplicate=duplicate)


def test_pos_contract_has_all_vendor_operations():
    adapter = _LocalPosFixture()
    assert isinstance(adapter, PosAdapter)
    result = asyncio.run(adapter.push_order({"order_id": "QB-1"}, "sync:QB-1"))
    assert result.accepted and result.external_id == "order-sync:QB-1"
    reference = asyncio.run(adapter.invoice_reference("invoice-1", "invoice:1"))
    assert reference == ExternalReference("local-fixture", "invoice-1")


def test_printer_contract_exposes_duplicate_result_for_retries():
    adapter = _LocalPrinterFixture()
    assert isinstance(adapter, PrinterAdapter)
    ticket = KitchenTicket(
        ticket_id="ticket-1",
        order_number="QB-1",
        station="Main Kitchen",
        lines=(TicketLine("1", "Meal"),),
        printed_at=datetime.now(UTC),
    )
    first = asyncio.run(adapter.print_ticket(ticket, "print:ticket-1"))
    duplicate = asyncio.run(adapter.print_ticket(ticket, "print:ticket-1"))
    assert first.accepted and not first.duplicate
    assert not duplicate.accepted and duplicate.duplicate


def test_connector_contract_values_are_immutable():
    result = SyncResult(accepted=True)
    with pytest.raises(FrozenInstanceError):
        result.accepted = False
