"""Small async Razorpay Orders/Payments/Refunds API adapter.

Secrets stay server-side. The Flutter SDK receives only a public key id and backend order.
"""

import hashlib
import hmac
from typing import Any

import httpx

from backend.domain.rules import BusinessError
from backend.integrations.payments.base import PaymentProvider
from backend.shared.settings import Settings


class RazorpayGateway(PaymentProvider):
    base_url = "https://api.razorpay.com/v1"

    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        if not settings.razorpay_enabled or settings.razorpay_mode == "disabled":
            raise BusinessError(
                "online_payment_unavailable", "Online payment is currently unavailable.", 503
            )
        self.settings = settings
        self.key_id = settings.razorpay_key_id.get_secret_value()
        self.key_secret = settings.razorpay_key_secret.get_secret_value()
        self.webhook_secrets = tuple(
            secret
            for secret in (
                settings.razorpay_webhook_secret.get_secret_value(),
                settings.razorpay_webhook_secret_previous.get_secret_value(),
            )
            if secret
        )
        self.transport = transport

    async def _request(self, method: str, path: str, *, json: dict | None = None) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                auth=(self.key_id, self.key_secret),
                timeout=httpx.Timeout(8.0, connect=3.0),
                transport=self.transport,
            ) as client:
                response = await client.request(method, path, json=json)
        except httpx.TimeoutException as exc:
            raise BusinessError(
                "payment_provider_timeout", "Payment provider status is uncertain", 503
            ) from exc
        except httpx.HTTPError as exc:
            raise BusinessError(
                "payment_provider_unavailable", "Payment provider is unavailable", 503
            ) from exc
        try:
            result = response.json()
        except ValueError as exc:
            raise BusinessError(
                "payment_provider_response", "Payment provider returned an invalid response", 502
            ) from exc
        if not response.is_success:
            # Never relay provider response bodies; they may contain customer or payment details.
            error = result.get("error") if isinstance(result, dict) else None
            code = error.get("code") if isinstance(error, dict) else None
            raise BusinessError(
                "payment_provider_rejected",
                f"Payment provider rejected the request ({code or response.status_code})",
                502,
            )
        if not isinstance(result, dict):
            raise BusinessError(
                "payment_provider_response", "Payment provider returned an invalid response", 502
            )
        return result

    async def create_order(self, amount_minor: int, currency: str, receipt: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/orders",
            json={"amount": amount_minor, "currency": currency, "receipt": receipt},
        )

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/payments/{payment_id}")

    async def capture_payment(
        self, payment_id: str, amount_minor: int, currency: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/payments/{payment_id}/capture",
            json={"amount": amount_minor, "currency": currency},
        )

    async def create_refund(
        self, payment_id: str, amount_minor: int, receipt: str
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/payments/{payment_id}/refund",
            json={"amount": amount_minor, "receipt": receipt},
        )

    def verify_checkout_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        expected = hmac.new(
            self.key_secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        if not signature or not self.webhook_secrets:
            return False
        return any(
            hmac.compare_digest(
                hmac.new(secret.encode(), body, hashlib.sha256).hexdigest(), signature
            )
            for secret in self.webhook_secrets
        )
