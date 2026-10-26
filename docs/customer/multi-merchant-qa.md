# Multi-merchant cart QA

Date: 2026-10-26. API integration uses local `quickbuddy_test` only.

## Backend verified

- A single customer cart can contain lines for separate branches and windows.
- Quote snapshot includes merchant/branch, window and address context.
- Confirmation creates one parent order with merchant child orders/fulfillment units and reserves inventory under the existing transaction/idempotency path.
- The test suite covers two-merchant, separate-window confirmation and duplicate-confirm idempotency. Customer catalogue/cart integration also checks cart version, quote enrichment and owner isolation.
- Reorder reads only the owner’s historical lines. The client checks currently saved addresses and obtains current branch windows before adding; the new quote remains authoritative.

Result: `tests/integration` **29 passed** (55.28 s) on 2026-10-26. Targeted customer catalog/cart/quote/payment/reorder authorization test: **1 passed**. Unit/backend suite: **40 passed**.

## Customer UX behavior

Cart lines are grouped by branch in collapsible sections. Each group displays its delivery method and time window. Checkout uses a single action and grouped server quote; separate deliveries are disclosed. Quantity edits send expected cart version and then reload canonical cart state. A stale/invalid line fails through backend quote rather than being silently repriced by the client.

## Gaps that remain

- Flutter execution/screenshot QA unavailable; no actual rapid-tap race was run on a device.
- No in-place line edit for address/method/window. Re-add is required.
- Fee, tax, discount and delivery charge breakdown is not returned per merchant. App does not fabricate it.
- API currently does not expose independent child cancellation/refund UX or a partial merchant-unavailable recovery endpoint preserving unaffected lines in a guided flow.
- Recurring/subscription orders and ASAP are not implemented.

No claim is made that the full multi-merchant flow was exercised from rendered Flutter app.
