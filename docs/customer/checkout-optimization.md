# Checkout optimization

Date: 2026-10-26.

## Implemented flow

Current catalogue product → choose a backend-returned future window and pickup/courier details (or conditional saved-choice quick-add) → server quote → merchant-group review → explicit sandbox order confirmation in development/test. Cart ID and quote-scoped idempotency key are kept in platform secure storage. The backend owns prices, availability, quote, order split and payment status.

The customer app shows each merchant, line quantity/unit price/line total, a merchant subtotal calculated from quote lines, consolidated server total, quote expiry, and the sandbox/payment-unavailable state. It warns that merchants may deliver separately and does not invent a shared delivery charge, tax, fee or discount. The final action is clearly named “Place sandbox order”; no payment is automatic.

## Tap estimate

See [ux-flow-analysis.md](ux-flow-analysis.md). The returning customer path drops from an estimated five to four explicit activations by removing the per-add choice sheet when the saved choice remains valid. Counts are source-derived estimates, not telemetry. Checkout still requires review and explicit confirmation.

## Reliability behavior and limitations

- `POST /orders/confirm` receives a persisted quote-scoped `Idempotency-Key`, so retry of the same quote reuses the same key.
- After order creation, dev/test flow creates or retrieves sandbox intent and invokes a server-side signed completion; the order screen can recover an existing payment after app restart.
- If confirmation response is lost, current retry uses same quote/key. The UI does not yet proactively query a dedicated idempotency result endpoint before retry; server idempotency is the protection.
- Quote is refreshed on checkout entry/retry and order confirmation revalidates backend state. Cart-line edits use expected cart version.
- Production payment provider and payment preference are not configured. Current API does not provide per-merchant fee/tax/discount breakdown; only authoritative returned quote values can be displayed.
- Cart line address, method and window cannot be changed in place. Separate merchant windows are supported, ASAP and recurring scheduling are not.

## Verification

Backend integration verifies live price/stock catalogue, cart reload/version, quote lines, signed sandbox status, reorder and cross-customer denials. The complete integration run passed 29 tests on 2026-10-26. Flutter analyzer/widget/build and device checkout were unavailable; do not infer a complete mobile purchase from API tests.
