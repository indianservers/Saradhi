# Phase 8 finance architecture audit

## Existing assets

- `finance.payment_intents` is the parent-order payment record with provider, currency, amount, refunded amount, and provider reference. `(order_id, provider)` is unique.
- Existing supplemental tables include payment attempts, authorizations, captures, reconciliations, refund allocations, merchant payables, pilot payables, settlement batches/lines, tax rules, invoices, credit notes, and ledger posting batches.
- Double-entry journals already enforce per-currency balancing, one book/legal entity per journal, idempotency, currency scale, immutable posted entries, and explicit reversal entries.
- Existing refund approval is maker-checker; refund execution is currently sandbox-only and rejects cross-organization parent orders unless allocations are added.
- Customer checkout confirms an order before payment. Online payment is therefore a separate payment obligation and current order confirmation must not be interpreted as captured funds.

## Phase 8 code added

- Server-only Razorpay Orders/Payments adapter, disabled/test/live configuration guards, Razorpay Flutter checkout wiring, authoritative callback signature plus provider-status verification, and signed webhook inbox with deduplication and unmatched reference retention.
- A migration adds `finance.razorpay_webhook_events`; no duplicate ledger was created.

## Known gaps

COD/COS cash custody and reconciliation; Razorpay refund execution/reconciliation; merchant allocation and partial merchant rejection refunds; commission/tax rule resolution and snapshots; payroll/settlement calculation and approval APIs; company/merchant/pilot real finance reports; Route and payout integrations; journal postings from captured payment, refunds, commissions, and settlements. These remain unavailable and are not simulated.

## Safe handling

Live Razorpay requests stay disabled without server-side configuration. Route and payout flags are rejected at boot. Razorpay secrets are never returned to client APIs. No live credentials or transactions were used.
