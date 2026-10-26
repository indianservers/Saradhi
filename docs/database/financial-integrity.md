# Financial integrity and boundaries

Money is stored as `Numeric(20,4)` and handled as Decimal with currency-scale validation and
explicit half-even rounding. Posted ledger journals must balance independently per currency and
stay within one legal-entity book. Deferred database triggers reject unbalanced posts even when
service checks are bypassed. Posted records and lines are immutable; correction uses an
idempotent reversal. Refunds serialize on the payment and require an approved matching request
from a different actor; cumulative refunds cannot exceed confirmed funds.

Real PostgreSQL tests covered valid and invalid journals, database-level deferred balance
rejection, journal immutability/reversal, signed sandbox webhook deduplication, duplicate refund
idempotency and partial refund approval. The sandbox adapter is deterministic, makes no external
financial calls and is disabled in production. No actual gateway, charge, settlement or payout
was used. Payment settlement/reconciliation and automatic order-to-ledger posting are not
implemented.

For a multi-merchant order, a rejected child remains rejected and another child remains pending;
the parent sandbox payment-intent route returns `revised_payment_required` and creates no payment
intent. Refunds spanning multiple merchant organizations return
`allocated_refund_required`. Merchant allocation, revised payable amount, per-child refunds,
settlement and ledger allocations are launch blockers, not implicitly covered by the single
merchant partial-refund test.

See `financial-ledger.md` and the sandbox refund integration tests. Production launch requires
an approved chart of accounts, currency/tax policy, gateway adapter/idempotency, reconciliation,
allocation and settlement workflows with independently reviewed evidence.
