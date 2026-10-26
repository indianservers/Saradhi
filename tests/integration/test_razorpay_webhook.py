import hashlib
import hmac
import json
from decimal import Decimal
from uuid import uuid4

from pydantic import SecretStr
from sqlalchemy import select

from backend.persistence import models as m
from tests.integration.helpers import checkout, world


async def test_razorpay_webhook_authenticates_deduplicates_and_records_unmatched(api):
    client, app = api
    app.state.settings = app.state.settings.model_copy(
        update={
            "razorpay_enabled": True,
            "razorpay_mode": "test",
            "razorpay_key_id": SecretStr("rzp_test_public"),
            "razorpay_key_secret": SecretStr("controlled-test-secret"),
            "razorpay_webhook_secret": SecretStr("controlled-webhook-secret"),
        }
    )
    body = json.dumps(
        {
            "entity": "event",
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_unmatched123",
                        "order_id": "order_unmatched123",
                        "amount": 5000,
                        "currency": "INR",
                        "status": "captured",
                    }
                }
            },
        },
        separators=(",", ":"),
    ).encode()
    event_id = f"evt-unmatched-{uuid4().hex}"
    headers = {"X-Razorpay-Event-Id": event_id}
    invalid = await client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={**headers, "X-Razorpay-Signature": "0" * 64},
    )
    assert invalid.status_code == 401

    signature = hmac.new(b"controlled-webhook-secret", body, hashlib.sha256).hexdigest()
    accepted = await client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={**headers, "X-Razorpay-Signature": signature},
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "unmatched"

    duplicate = await client.post(
        "/api/v1/payments/razorpay/webhook",
        content=body,
        headers={**headers, "X-Razorpay-Signature": signature},
    )
    assert duplicate.status_code == 200, duplicate.text
    assert duplicate.json()["duplicate"] is True

    async with app.state.sessions() as db:
        record = await db.scalar(
            select(m.RazorpayWebhookEvent).where(m.RazorpayWebhookEvent.event_id == event_id)
        )
        assert record.status == "unmatched"
        assert record.payment_id is None


async def test_online_configuration_is_disabled_without_keys(api):
    client, app = api
    from tests.integration.helpers import user

    customer = await user(client, app)
    response = await client.get("/api/v1/payments/configuration", headers=customer["headers"])
    assert response.status_code == 200
    assert response.json()["online_payment_available"] is False
    assert response.json()["key_id"] is None
    assert response.json()["message"] == "Online payment is currently unavailable."


async def test_customer_payment_order_uses_backend_amount_and_verifies_capture(api):
    client, app = api
    state = await world(client, app, 1)
    _, _, order, _ = await checkout(client, state["customer"], state["shops"])
    provider_order_id = "order_" + uuid4().hex
    provider_payment_id = "pay_" + uuid4().hex
    app.state.settings = app.state.settings.model_copy(
        update={
            "razorpay_enabled": True,
            "razorpay_mode": "test",
            "razorpay_key_id": SecretStr("rzp_test_public"),
            "razorpay_key_secret": SecretStr("controlled-test-secret"),
            "razorpay_webhook_secret": SecretStr("controlled-webhook-secret"),
        }
    )

    class FakeGateway:
        key_id = "rzp_test_public"

        def __init__(self, settings):
            self.settings = settings
            self.calls = 0
            self.payment = {}

        async def create_order(self, amount_minor, currency, receipt):
            self.calls += 1
            self.payment = {
                "id": provider_payment_id,
                "order_id": provider_order_id,
                "amount": amount_minor,
                "currency": currency,
                "status": "captured",
            }
            return {"id": provider_order_id, "amount": amount_minor, "currency": currency}

        async def fetch_payment(self, payment_id):
            assert payment_id == self.payment["id"]
            return self.payment

        async def capture_payment(self, payment_id, amount_minor, currency):
            raise AssertionError("captured fixture must not be captured again")

        def verify_checkout_signature(self, order_id, payment_id, signature):
            return signature == "a" * 64

        def verify_webhook_signature(self, payload, signature):
            return signature == "b" * 64

    fake = FakeGateway(app.state.settings)
    app.state.razorpay_gateway_factory = lambda _settings: fake
    headers = {**state["customer"]["headers"], "Idempotency-Key": "razorpay-attempt-0001"}
    created = await client.post(
        "/api/v1/payments/intents", json={"order_id": order["id"]}, headers=headers
    )
    assert created.status_code == 200, created.text
    assert created.json()["provider_order_id"] == provider_order_id
    assert created.json()["key_id"] == "rzp_test_public"
    assert created.json()["amount_minor"] == int(Decimal(order["total"]) * 100)
    assert fake.calls == 1

    repeated = await client.post(
        "/api/v1/payments/intents",
        json={"order_id": order["id"]},
        headers={**state["customer"]["headers"], "Idempotency-Key": "razorpay-attempt-0002"},
    )
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["provider_order_id"] == created.json()["provider_order_id"]
    assert fake.calls == 1

    verified = await client.post(
        "/api/v1/payments/razorpay/verify",
        json={
            "order_id": provider_order_id,
            "payment_id": provider_payment_id,
            "signature": "a" * 64,
        },
        headers=state["customer"]["headers"],
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["status"] == "confirmed"

    for event_type in ("payment.authorized", "payment.failed"):
        event_body = json.dumps(
            {
                "entity": "event",
                "event": event_type,
                "payload": {
                    "payment": {
                        "entity": {
                            "id": provider_payment_id,
                            "order_id": provider_order_id,
                            "amount": created.json()["amount_minor"],
                            "currency": "XTS",
                            "status": event_type.split(".")[1],
                        }
                    }
                },
            },
            separators=(",", ":"),
        ).encode()
        event_response = await client.post(
            "/api/v1/payments/razorpay/webhook",
            content=event_body,
            headers={
                "X-Razorpay-Event-Id": f"evt-late-{uuid4().hex}",
                "X-Razorpay-Signature": "b" * 64,
            },
        )
        assert event_response.status_code == 200, event_response.text
        assert event_response.json()["status"] == "processed"
    status = await client.get(
        f"/api/v1/payments/{created.json()['id']}", headers=state["customer"]["headers"]
    )
    assert status.json()["status"] == "confirmed"
