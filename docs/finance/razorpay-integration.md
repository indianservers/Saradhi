# Razorpay integration

The provider adapter is `backend/integrations/payments/razorpay.py`. It uses TLS-verified HTTPS, bounded timeouts, server-side Basic Auth, no automatic request retries, and does not relay provider response bodies or credentials. Its surface covers Orders creation, payment fetch/capture, refund request primitive, checkout HMAC, and webhook HMAC with current/previous webhook secrets.

`POST /api/v1/payments/intents` requires an authenticated order owner and an `Idempotency-Key`. The backend reads the persisted order total and currency scale, persists a payment intent and attempt before making the provider call, then stores the Razorpay order id. Timed-out attempts are marked uncertain and cannot be blindly retried. Flutter receives only the public key id and provider order reference.

`POST /api/v1/payments/razorpay/verify` checks checkout HMAC using the server key secret, fetches payment status from Razorpay, checks remote order/amount/currency, captures an authorized payment when auto-capture is enabled, then fetches again. Only captured payments become internally `confirmed`; authorization remains non-final.

The webhook route validates the exact raw request bytes and event id, deduplicates by Razorpay event id and body hash, stores unmatched payment references, handles captured/authorized/failed payment events monotonically, and records capture references. Refund webhook intake is retained but refund accounting is not yet implemented.

The integration follows Razorpay's documented server-created Orders flow, checkout HMAC construction, and backend status verification. See [Razorpay Python integration](https://razorpay.com/docs/server-integration/python/test-app/) and [Razorpay webhook guidance](https://razorpay.com/docs/webhooks/).
