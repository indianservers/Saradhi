# Phase 8 test results

## Executed

- Deterministic adapter tests use `httpx.MockTransport`; they verify disabled mode fails closed, correct checkout HMAC, active/previous webhook secrets, minor-unit order creation, Basic Auth presence, and provider error redaction.
- PostgreSQL API integration tests verify disabled configuration returns no key id, forged webhook signatures return 401, valid unmatched webhooks are durably recorded, duplicate event delivery is idempotent, customer payment order amount comes from the stored order, a repeat does not create a second provider order, and captured provider status is recorded after checkout verification.
- Migration `20261026_0016` applied to local dev and the guarded PostgreSQL integration database.
- Full backend suite after migration and contract updates: 87 passed with one pre-existing Starlette/httpx deprecation warning.
- Ruff checks for the modified Python adapter, orchestration, routes, settings, models, and tests passed; workspace TypeScript typecheck and OpenAPI export passed.

## Not executed

No real Razorpay request was sent; no credentials were supplied. Flutter/Dart executables are unavailable in this environment, so the Razorpay Flutter plugin dependency and UI changes could not be resolved or compiled here. Route/payout, refund, COD, tax, commission, and settlement workflows are not fully implemented or testable in this phase slice.
