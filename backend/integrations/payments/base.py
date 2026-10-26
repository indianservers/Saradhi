"""Provider-neutral contract used by payment orchestration."""

from typing import Any, Protocol


class PaymentProvider(Protocol):
    key_id: str

    async def create_order(
        self, amount_minor: int, currency: str, receipt: str
    ) -> dict[str, Any]: ...

    async def fetch_payment(self, payment_id: str) -> dict[str, Any]: ...

    async def capture_payment(
        self, payment_id: str, amount_minor: int, currency: str
    ) -> dict[str, Any]: ...

    async def create_refund(
        self, payment_id: str, amount_minor: int, receipt: str
    ) -> dict[str, Any]: ...

    def verify_checkout_signature(self, order_id: str, payment_id: str, signature: str) -> bool: ...

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool: ...
