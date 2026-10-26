# Double-entry ledger

The existing ledger remains the accounting source of truth. Journals are idempotent, balanced per currency, restricted to one book/legal entity, precision-checked, immutable after posting, and reversible only by a new reversal journal. Posted data is not rewritten by this phase.

Phase 8 has not yet added source-specific ledger posting for Razorpay captures, cash held by pilots, merchant/pilot payables, commissions, tax liabilities, gateway fees, refunds, or settlement confirmations. A payment intent/capture record is not itself a ledger posting. Do not represent balances as a separate mutable wallet.
