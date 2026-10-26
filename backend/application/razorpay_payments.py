"""Persistence and state-transition orchestration around the Razorpay adapter."""

import hashlib
import json
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select

from backend.application.common import add, event, now, owned
from backend.domain.rules import BusinessError
from backend.integrations.payments.base import PaymentProvider
from backend.persistence import models as m
from backend.persistence.foundations import FOUNDATION_MODELS as F
from backend.persistence.repositories import Repository


def to_minor_units(amount: Decimal, scale: int) -> int:
    minor = amount * (10**scale)
    if minor != minor.to_integral_value() or minor <= 0:
        raise BusinessError(
            "currency_precision", "Amount cannot be represented in currency subunits", 422
        )
    return int(minor)


async def create_order(
    sessions,
    actor,
    order_id: UUID,
    idempotency_key: str,
    request_id: str,
    gateway: PaymentProvider,
):
    async with sessions.begin() as db:
        order = await Repository(db).require(m.Order, order_id, lock=True)
        owned(actor, order.user_id)
        if order.status != "confirmed":
            raise BusinessError("invalid_order", "Order is not payable")
        rejected = await db.scalar(
            select(m.MerchantOrder.id).where(
                m.MerchantOrder.order_id == order.id,
                m.MerchantOrder.status.in_(("rejected", "cancelled")),
            )
        )
        if rejected:
            raise BusinessError(
                "revised_payment_required", "Order allocations changed; revise checkout first"
            )
        payment = await db.scalar(
            select(m.PaymentIntent)
            .where(
                m.PaymentIntent.order_id == order.id,
                m.PaymentIntent.provider == "razorpay",
            )
            .with_for_update()
        )
        if payment and payment.provider_reference:
            if payment.status == "failed":
                # Retry the existing Razorpay order; never create a second charge order.
                payment.status = "pending"
            currency = await db.scalar(
                select(m.Currency).where(m.Currency.code == payment.currency)
            )
            return _intent_result(payment, gateway, currency.scale)
        if not payment:
            payment = await add(
                db,
                m.PaymentIntent,
                order_id=order.id,
                provider="razorpay",
                status="pending",
                currency=order.currency,
                amount=order.total,
                refunded=Decimal("0"),
                provider_reference=None,
            )
            await db.flush()
        attempt_model = F["finance.payment_attempts"]
        attempt = await db.scalar(
            select(attempt_model).where(
                attempt_model.payment_id == payment.id,
                attempt_model.idempotency_key == idempotency_key,
            )
        )
        if attempt:
            if attempt.status == "failed":
                raise BusinessError(
                    "payment_attempt_failed",
                    "This payment attempt failed. Start a new attempt to continue.",
                    409,
                )
            raise BusinessError(
                "payment_attempt_uncertain",
                "Payment order creation has an uncertain result; contact support before retrying",
                409,
            )
        active_attempt = await db.scalar(
            select(attempt_model)
            .where(
                attempt_model.payment_id == payment.id,
                attempt_model.status.in_(("started", "uncertain")),
            )
            .limit(1)
        )
        if active_attempt:
            raise BusinessError(
                "payment_attempt_uncertain", "Payment order creation is still being reconciled", 409
            )
        currency = await db.scalar(select(m.Currency).where(m.Currency.code == order.currency))
        if currency is None:
            raise BusinessError("currency_not_found", "Order currency is not configured", 422)
        amount_minor = to_minor_units(order.total, currency.scale)
        attempt = await add(
            db,
            attempt_model,
            payment_id=payment.id,
            idempotency_key=idempotency_key,
            status="started",
            provider_reference=None,
        )
        payment_id = payment.id
        currency_code = payment.currency

    try:
        remote = await gateway.create_order(amount_minor, currency_code, payment_id.hex)
        provider_order_id = remote.get("id")
        if (
            not isinstance(provider_order_id, str)
            or not provider_order_id.startswith("order_")
            or remote.get("amount") != amount_minor
            or remote.get("currency") != currency_code
        ):
            raise BusinessError(
                "payment_provider_response",
                "Payment provider returned an order that did not match the checkout",
                502,
            )
    except Exception as exc:
        async with sessions.begin() as db:
            persisted = await db.get(attempt_model, attempt.id)
            if persisted:
                persisted.status = (
                    "failed"
                    if getattr(exc, "code", "") == "payment_provider_rejected"
                    else "uncertain"
                )
        raise

    async with sessions.begin() as db:
        payment = await Repository(db).require(m.PaymentIntent, payment_id, lock=True)
        attempt = await Repository(db).require(attempt_model, attempt.id, lock=True)
        payment.provider_reference = provider_order_id
        attempt.provider_reference = provider_order_id
        attempt.status = "created"
        await event(
            db,
            "payment.order_created",
            payment.id,
            request_id,
            order_id=payment.order_id,
            provider="razorpay",
        )
        return _intent_result(payment, gateway, currency.scale)


def _intent_result(payment, gateway, scale):
    return {
        "id": str(payment.id),
        "order_id": str(payment.order_id),
        "status": payment.status,
        "provider": payment.provider,
        "provider_order_id": payment.provider_reference,
        "key_id": gateway.key_id,
        "amount_minor": to_minor_units(payment.amount, scale),
        "currency": payment.currency,
        "mode": gateway.settings.razorpay_mode,
    }


async def verify_checkout(
    sessions,
    actor,
    provider_order_id: str,
    provider_payment_id: str,
    signature: str,
    request_id: str,
    gateway: PaymentProvider,
):
    async with sessions() as db:
        payment = await db.scalar(
            select(m.PaymentIntent).where(
                m.PaymentIntent.provider == "razorpay",
                m.PaymentIntent.provider_reference == provider_order_id,
            )
        )
        if not payment:
            raise BusinessError("payment_not_found", "Payment order was not found", 404)
        order = await Repository(db).require(m.Order, payment.order_id)
        owned(actor, order.user_id)
        payment_id = payment.id
        currency_code = payment.currency
        expected_amount = payment.amount
        currency = await db.scalar(select(m.Currency).where(m.Currency.code == currency_code))
        if currency is None:
            raise BusinessError("currency_not_found", "Payment currency is not configured", 422)
        expected_minor = to_minor_units(expected_amount, currency.scale)
    if not gateway.verify_checkout_signature(provider_order_id, provider_payment_id, signature):
        raise BusinessError("invalid_payment_signature", "Payment signature is invalid", 401)
    remote = await gateway.fetch_payment(provider_payment_id)
    if remote.get("order_id") != provider_order_id:
        raise BusinessError("payment_mismatch", "Payment does not belong to this checkout", 422)
    if remote.get("amount") != expected_minor or remote.get("currency") != currency_code:
        raise BusinessError(
            "payment_mismatch", "Provider payment amount or currency does not match", 422
        )
    if remote.get("status") == "authorized" and gateway.settings.razorpay_auto_capture:
        await gateway.capture_payment(provider_payment_id, expected_minor, currency_code)
        remote = await gateway.fetch_payment(provider_payment_id)
    status = remote.get("status")
    if status not in {"authorized", "captured", "failed"}:
        status = "pending"
    async with sessions.begin() as db:
        payment = await Repository(db).require(m.PaymentIntent, payment_id, lock=True)
        capture_model = F["finance.payment_captures"]
        if status == "captured":
            newly_captured = payment.status != "confirmed"
            payment.status = "confirmed"
            existing = await db.scalar(
                select(capture_model.id).where(
                    capture_model.provider_reference == provider_payment_id
                )
            )
            if not existing:
                await add(
                    db,
                    capture_model,
                    payment_id=payment.id,
                    amount=expected_amount,
                    provider_reference=provider_payment_id,
                )
            if newly_captured:
                await event(
                    db,
                    "payment.captured",
                    payment.id,
                    request_id,
                    order_id=payment.order_id,
                    provider="razorpay",
                )
        elif payment.status != "confirmed":
            payment.status = status
        return payment


async def receive_webhook(
    sessions,
    payload: bytes,
    event_id: str,
    signature: str,
    request_id: str,
    gateway: PaymentProvider,
):
    if not gateway.verify_webhook_signature(payload, signature):
        raise BusinessError("invalid_webhook_signature", "Webhook signature is invalid", 401)
    try:
        data = json.loads(payload)
        event_type = data.get("event")
        if not isinstance(event_type, str):
            raise ValueError
        entity_key = "payment" if event_type.startswith("payment.") else "refund"
        entity = data["payload"][entity_key]["entity"]
        if not isinstance(entity, dict):
            raise ValueError
    except (ValueError, TypeError, KeyError) as exc:
        raise BusinessError("invalid_webhook", "Webhook payload is invalid", 422) from exc
    is_refund_event = event_type.startswith("refund.")
    provider_payment_id = entity.get("payment_id") if is_refund_event else entity.get("id")
    provider_order_id = entity.get("order_id")
    if not isinstance(provider_payment_id, str) or not provider_payment_id.startswith("pay_"):
        raise BusinessError("invalid_webhook", "Webhook payment reference is invalid", 422)
    payload_hash = hashlib.sha256(payload).hexdigest()
    async with sessions.begin() as db:
        inbox = m.RazorpayWebhookEvent
        prior = await db.scalar(select(inbox).where(inbox.event_id == event_id).with_for_update())
        if prior:
            if prior.payload_hash != payload_hash:
                raise BusinessError(
                    "webhook_conflict", "Event identifier was reused with another body", 409
                )
            return {"accepted": True, "duplicate": True, "status": prior.status}
        capture_model = F["finance.payment_captures"]
        payment_id_from_capture = (
            await db.scalar(
                select(capture_model.payment_id).where(
                    capture_model.provider_reference == provider_payment_id
                )
            )
            if is_refund_event
            else None
        )
        if is_refund_event and payment_id_from_capture:
            payment = await db.scalar(
                select(m.PaymentIntent)
                .where(m.PaymentIntent.id == payment_id_from_capture)
                .with_for_update()
            )
        elif provider_order_id:
            payment = await db.scalar(
                select(m.PaymentIntent)
                .where(
                    m.PaymentIntent.provider == "razorpay",
                    m.PaymentIntent.provider_reference == provider_order_id,
                )
                .with_for_update()
            )
        else:
            payment = None
        record = await add(
            db,
            inbox,
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            payment_id=payment.id if payment else None,
            provider_payment_id=provider_payment_id,
            provider_order_id=provider_order_id,
            status="unmatched" if not payment else "received",
        )
        if not payment:
            return {"accepted": True, "duplicate": False, "status": record.status}
        if is_refund_event:
            record.status = "ignored"
            record.error_code = "refund_workflow_unavailable"
            record.processed_at = now()
            return {"accepted": True, "duplicate": False, "status": record.status}
        currency = await db.scalar(select(m.Currency).where(m.Currency.code == payment.currency))
        if currency is None:
            record.status, record.error_code = "rejected", "currency_not_configured"
            return {"accepted": True, "duplicate": False, "status": record.status}
        amount = Decimal(entity.get("amount", 0)) / (10**currency.scale)
        if entity.get("currency") != payment.currency or amount != payment.amount:
            record.status, record.error_code = "rejected", "payment_mismatch"
            return {"accepted": True, "duplicate": False, "status": record.status}
        if event_type == "payment.captured":
            newly_captured = payment.status != "confirmed"
            payment.status = "confirmed"
            existing = await db.scalar(
                select(capture_model.id).where(
                    capture_model.provider_reference == provider_payment_id
                )
            )
            if not existing:
                await add(
                    db,
                    capture_model,
                    payment_id=payment.id,
                    amount=payment.amount,
                    provider_reference=provider_payment_id,
                )
            if newly_captured:
                await event(
                    db,
                    "payment.captured",
                    payment.id,
                    request_id,
                    order_id=payment.order_id,
                    provider="razorpay",
                )
        elif event_type == "payment.authorized":
            if payment.status != "confirmed":
                payment.status = "authorized"
        elif event_type == "payment.failed":
            if payment.status not in {"confirmed", "refunded"}:
                payment.status = "failed"
        else:
            record.status = "ignored"
            record.processed_at = now()
            return {"accepted": True, "duplicate": False, "status": record.status}
        record.status = "processed"
        record.processed_at = now()
        return {"accepted": True, "duplicate": False, "status": record.status}
