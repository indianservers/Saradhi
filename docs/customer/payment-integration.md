# Payment integration

The customer app creates the order using the backend quote and idempotent confirmation API, then calls `POST /api/v1/finance/sandbox/payment-intents` for the returned order ID. In development/test only, it can call authenticated `POST /api/v1/finance/sandbox/payments/{payment_id}/complete`. This endpoint verifies order ownership, creates a deterministic sandbox event, signs it with the server-only secret and processes it through the existing idempotent webhook handler. Repeated calls return the already processed payment.

The sandbox gateway requires non-production configuration and a server-side secret. The completion endpoint rejects production. This simulation has no real financial effect and must not be represented as a production payment provider. Production payment is not complete until a real gateway and verified provider callback are configured.

The backend supports payment status lookup at `GET /api/v1/finance/payments/{payment_id}` and signed webhook ingestion at `POST /api/v1/finance/sandbox/webhook`. No refund endpoint is exposed to the customer; refunds remain approval-controlled.
