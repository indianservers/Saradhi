import hashlib
import hmac

import httpx
import pytest

from backend.domain.rules import BusinessError
from backend.integrations.payments.razorpay import RazorpayGateway
from backend.shared.settings import Settings


def settings(**updates):
    values = {
        "app_env": "test",
        "database_url": "postgresql+asyncpg://test:secret@127.0.0.1:5432/quickbuddy_test",
        "razorpay_enabled": True,
        "razorpay_mode": "test",
        "razorpay_key_id": "rzp_test_public",
        "razorpay_key_secret": "not-a-real-key-secret",
        "razorpay_webhook_secret": "webhook-current",
        "razorpay_webhook_secret_previous": "webhook-previous",
    }
    values.update(updates)
    return Settings(**values)


def test_disabled_gateway_fails_closed_without_network():
    with pytest.raises(BusinessError) as exc:
        RazorpayGateway(Settings())
    assert exc.value.code == "online_payment_unavailable"


def test_checkout_and_rotating_webhook_signatures():
    gateway = RazorpayGateway(settings())
    raw = b'{"event":"payment.captured"}'
    old_signature = hmac.new(b"webhook-previous", raw, hashlib.sha256).hexdigest()
    assert gateway.verify_webhook_signature(raw, old_signature)
    assert not gateway.verify_webhook_signature(raw, "f" * 64)
    checkout_signature = hmac.new(
        b"not-a-real-key-secret", b"order_12345678|pay_12345678", hashlib.sha256
    ).hexdigest()
    assert gateway.verify_checkout_signature("order_12345678", "pay_12345678", checkout_signature)
    assert not gateway.verify_checkout_signature(
        "order_other123", "pay_12345678", checkout_signature
    )


async def test_create_order_sends_minor_units_and_redacts_provider_errors():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        seen["json"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "id": "order_12345678",
                "amount": 12345,
                "currency": "INR",
            },
        )

    gateway = RazorpayGateway(settings(), transport=httpx.MockTransport(handler))
    order = await gateway.create_order(12345, "INR", "receipt0000000000000000000000000000")
    assert order["id"] == "order_12345678"
    assert seen["path"] == "/v1/orders"
    assert '"amount":12345' in seen["json"]
    assert "not-a-real-key-secret" not in seen["json"]
    assert seen["auth"].startswith("Basic ")

    def rejected(_request):
        return httpx.Response(
            400,
            json={"error": {"code": "BAD_REQUEST_ERROR", "description": "sensitive provider text"}},
        )

    failing = RazorpayGateway(settings(), transport=httpx.MockTransport(rejected))
    with pytest.raises(BusinessError) as exc:
        await failing.create_order(100, "INR", "receipt0000000000000000000000000000")
    assert "sensitive provider text" not in exc.value.message
    assert exc.value.status == 502


def test_live_configuration_needs_production_approval_and_webhook_secret():
    with pytest.raises(ValueError):
        settings(razorpay_mode="live", app_env="test", razorpay_live_approval=True)
    with pytest.raises(ValueError):
        settings(
            razorpay_mode="live",
            app_env="production",
            razorpay_live_approval=True,
            database_url="postgresql+asyncpg://q:secret@db.example/quickbuddy",
            database_ssl=True,
            oidc_issuer="https://issuer.example",
            oidc_audience="quickbuddy",
            oidc_jwks_url="https://issuer.example/jwks",
            cors_origins=["https://admin.example"],
            razorpay_webhook_secret="",
        )
