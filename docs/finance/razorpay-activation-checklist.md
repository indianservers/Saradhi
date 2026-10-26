# Razorpay activation checklist

## Before test mode

- Confirm the Razorpay merchant account and permitted payment methods.
- Add test `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and a webhook secret through the deployment secret manager; do not commit them or put them in Flutter build variables.
- Set `RAZORPAY_ENABLED=true`, `RAZORPAY_MODE=test`, and keep Route/payout flags false.
- Register the HTTPS `/api/v1/payments/razorpay/webhook` URL in Razorpay test mode and subscribe to `payment.authorized`, `payment.captured`, `payment.failed`, and selected refund events.
- Verify a test payment, invalid checkout signature rejection, webhook signature rejection, duplicate delivery handling, uncertain timeout recovery, and captured state from a backend fetch.
- Verify refund behavior only after the refund engine is implemented and tested.

## Before live activation

- Complete production policies and regulatory/tax review, merchant settlement and refund controls, operational alerting, reconciliation, support runbooks, and production security testing.
- Verify production TLS, webhook URL/mode and secrets, Dashboard capture settings, payment methods, refund permissions, support process, and reconciliation access.
- Obtain explicit go-live approval. Set production-only live keys, `RAZORPAY_MODE=live`, `RAZORPAY_ENABLED=true`, and `RAZORPAY_LIVE_APPROVAL=true` in a secret manager.
- Keep `RAZORPAY_ROUTE_ENABLED=false` and `RAZORPAY_PAYOUTS_ENABLED=false` until separately implemented and approved.
- Run a controlled pre-production test and document the first live transaction/reconciliation before broad release.

This repository has no credentials; no live transaction was attempted.
