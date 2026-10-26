import hashlib
import hmac
import json
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy import select

from backend.application.common import add, event, now, owned, scoped
from backend.domain.rules import BusinessError, balanced, money
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


class PaymentGateway(Protocol):
    def verify_webhook(self, payload: bytes, signature: str) -> dict: ...
    async def refund(self, payment_reference: str, amount: Decimal, key: str) -> str: ...


class SandboxGateway:
    """Deterministic TEST ONLY adapter: no external financial effects."""

    def __init__(self, settings):
        if settings.app_env == "production" or not settings.sandbox_payments_enabled:
            raise BusinessError("sandbox_disabled", "Sandbox payments are disabled", 503)
        self.secret = settings.sandbox_webhook_secret.get_secret_value()
        if len(self.secret) < 32:
            raise BusinessError("sandbox_unconfigured", "Configure a sandbox webhook secret", 503)

    def verify_webhook(self, payload, signature):
        expected = hmac.new(self.secret.encode(), payload, "sha256").hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise BusinessError("invalid_webhook", "Webhook signature is invalid", 401)
        try:
            data = json.loads(payload)
            if not isinstance(data, dict) or not isinstance(data.get("event_id"), str):
                raise ValueError("Invalid event identifier")
            if data["status"] != "confirmed" or not data["event_id"].startswith("SANDBOX:"):
                raise ValueError("Invalid sandbox event")
            UUID(data["payment_id"])
            amount = Decimal(data["amount"])
            if not amount.is_finite() or amount <= 0 or len(data["event_id"]) > 128:
                raise ValueError("Invalid amount")
            if not isinstance(data["currency"], str) or len(data["currency"]) != 3:
                raise ValueError("Invalid currency")
        except (KeyError, ValueError, TypeError, ArithmeticError) as exc:
            raise BusinessError("invalid_webhook", "Invalid sandbox webhook payload", 422) from exc
        return data

    async def refund(self, payment_reference, amount, key):
        return (
            "SANDBOX:refund:"
            + hashlib.sha256(f"{payment_reference}:{amount}:{key}".encode()).hexdigest()
        )


async def post_journal(session, organization_id, key, description, lines, reversal_of=None):
    """Positive debit / negative credit. Lock scope before dedupe and posting."""
    await session.scalar(
        select(m.Organization).where(m.Organization.id == organization_id).with_for_update()
    )
    existing = await session.scalar(
        select(m.Journal).where(
            m.Journal.organization_id == organization_id, m.Journal.idempotency_key == key
        )
    )
    if existing:
        existing_lines = (
            await session.execute(
                select(m.JournalLine.account_id, m.JournalLine.amount).where(
                    m.JournalLine.journal_id == existing.id
                )
            )
        ).all()
        if sorted((str(a), v) for a, v in existing_lines) != sorted((str(a), v) for a, v in lines):
            raise BusinessError("idempotency_conflict", "Journal key was used for different lines")
        return existing
    accounts = []
    for account_id, amount in lines:
        account = await Repository(session).require(m.LedgerAccount, account_id)
        if account.organization_id != organization_id:
            raise BusinessError(
                "account_scope", "Journal accounts must belong to its organization", 403
            )
        currency = await session.scalar(
            select(m.Currency).where(m.Currency.code == account.currency)
        )
        if money(amount, currency.scale) != amount:
            raise BusinessError(
                "currency_precision", "Journal amount exceeds currency precision", 422
            )
        accounts.append((account, amount))
    balanced([(account.currency, amount) for account, amount in accounts])
    if len({account.book_id for account, _ in accounts}) != 1:
        raise BusinessError(
            "mixed_ledger_books", "Journal must use one legal entity and currency book", 422
        )
    journal = await add(
        session,
        m.Journal,
        organization_id=organization_id,
        book_id=accounts[0][0].book_id,
        idempotency_key=key,
        description=description,
        status="draft",
        reversal_of=reversal_of,
    )
    for account, amount in accounts:
        await add(
            session,
            m.JournalLine,
            journal_id=journal.id,
            organization_id=organization_id,
            account_id=account.id,
            currency=account.currency,
            amount=amount,
        )
    journal.status = "posted"
    await session.flush()  # Deferred database constraint rechecks final journal at COMMIT.
    return journal


async def reverse_journal(session, actor, journal_id, key):
    journal = await Repository(session).require(m.Journal, journal_id, lock=True)
    await scoped(session, actor, "finance.write", journal.organization_id)
    if journal.status != "posted":
        raise BusinessError("not_posted", "Only posted journals may be reversed")
    lines = (
        await session.execute(
            select(m.JournalLine.account_id, m.JournalLine.amount).where(
                m.JournalLine.journal_id == journal.id
            )
        )
    ).all()
    return await post_journal(
        session, journal.organization_id, key, "Reversal", [(a, -v) for a, v in lines], journal.id
    )


async def payment_intent(session, actor, order_id, gateway):
    order = await Repository(session).require(m.Order, order_id, lock=True)
    owned(actor, order.user_id)
    if order.status != "confirmed":
        raise BusinessError("invalid_order", "Order is not payable")
    rejected = await session.scalar(
        select(m.MerchantOrder.id).where(
            m.MerchantOrder.order_id == order.id,
            m.MerchantOrder.status.in_(["rejected", "cancelled"]),
        )
    )
    if rejected:
        raise BusinessError(
            "revised_payment_required", "Partial rejection requires revised payment allocations"
        )
    existing = await session.scalar(
        select(m.PaymentIntent).where(
            m.PaymentIntent.order_id == order.id, m.PaymentIntent.provider == "sandbox"
        )
    )
    if existing:
        return existing
    return await add(
        session,
        m.PaymentIntent,
        order_id=order.id,
        provider="sandbox",
        currency=order.currency,
        amount=order.total,
        provider_reference=f"SANDBOX:payment:{order.id}",
    )


async def webhook(session, gateway, payload, signature, request_id):
    data = gateway.verify_webhook(payload, signature)
    candidate = await Repository(session).require(m.PaymentIntent, UUID(data["payment_id"]))
    order = await Repository(session).require(m.Order, candidate.order_id, lock=True)
    payment = await Repository(session).require(
        m.PaymentIntent, UUID(data["payment_id"]), lock=True
    )
    payload_hash = hashlib.sha256(payload).hexdigest()
    prior = await session.scalar(
        select(m.Webhook).where(
            m.Webhook.provider == "sandbox", m.Webhook.event_id == data["event_id"]
        )
    )
    if prior:
        if prior.payload_hash != payload_hash:
            raise BusinessError("webhook_conflict", "Event identifier payload does not match")
        return payment
    if order.status != "confirmed" and payment.status != "confirmed":
        raise BusinessError("invalid_order", "Payment cannot confirm a cancelled order")
    if payment.status == "pending" and await session.scalar(
        select(m.MerchantOrder.id).where(
            m.MerchantOrder.order_id == order.id,
            m.MerchantOrder.status.in_(["rejected", "cancelled"]),
        )
    ):
        raise BusinessError(
            "revised_payment_required",
            "Rejected merchant orders require revised payment allocation",
        )
    if (
        payment.provider != "sandbox"
        or payment.currency != data["currency"]
        or payment.amount != Decimal(data["amount"])
    ):
        raise BusinessError("payment_mismatch", "Webhook does not match the payment intent", 422)
    if payment.status not in {"pending", "confirmed"}:
        raise BusinessError("payment_state", "Cannot confirm this payment")
    await add(
        session,
        m.Webhook,
        provider="sandbox",
        event_id=data["event_id"],
        payment_id=payment.id,
        payload_hash=payload_hash,
        processed_at=now(),
    )
    if payment.status == "pending":
        payment.status = "confirmed"
        await event(
            session,
            "payment.confirmed",
            payment.id,
            request_id,
            order_id=payment.order_id,
            provider="sandbox",
        )
    return payment


async def refund(
    session, actor, payment_id, amount, key, gateway, organization_id, request_id, approval_id
):
    await scoped(session, actor, "finance.write", organization_id)
    payment = await Repository(session).require(m.PaymentIntent, payment_id, lock=True)
    # A parent can span organizations: finance staff cannot refund somebody else's lines.
    children = (
        await session.execute(
            select(m.MerchantOrder, m.Branch.organization_id)
            .join(m.Branch)
            .where(m.MerchantOrder.order_id == payment.order_id)
        )
    ).all()
    if any(org != organization_id for _, org in children):
        raise BusinessError(
            "allocated_refund_required",
            "Multi-organization refunds require approved per-child allocations",
        )
    existing = await session.scalar(
        select(m.Refund).where(m.Refund.payment_id == payment.id, m.Refund.idempotency_key == key)
    )
    if existing:
        if existing.amount != amount or existing.approval_id != approval_id:
            raise BusinessError(
                "idempotency_conflict", "Refund key was used for a different amount"
            )
        return existing
    approval = await Repository(session).require(
        F["operations.refund_approval_requests"], approval_id, lock=True
    )
    if (
        approval.status != "approved"
        or approval.order_id != payment.order_id
        or approval.organization_id != organization_id
        or approval.amount != amount
    ):
        raise BusinessError(
            "refund_approval_required",
            "A matching separately approved refund request is required",
            403,
        )
    currency = await session.scalar(select(m.Currency).where(m.Currency.code == payment.currency))
    if (
        amount != money(amount, currency.scale)
        or amount <= 0
        or payment.refunded + amount > payment.amount
    ):
        raise BusinessError("refund_amount", "Invalid refund amount", 422)
    if payment.status != "confirmed":
        raise BusinessError("payment_state", "Only confirmed sandbox payments can be refunded")
    reference = await gateway.refund(payment.provider_reference, amount, key)
    record = await add(
        session,
        m.Refund,
        payment_id=payment.id,
        approval_id=approval.id,
        idempotency_key=key,
        amount=amount,
        status="sandbox_confirmed",
        provider_reference=reference,
    )
    payment.refunded += amount
    approval.status = "executed"
    await event(
        session, "refund.completed", record.id, request_id, provider="sandbox", amount=amount
    )
    return record
