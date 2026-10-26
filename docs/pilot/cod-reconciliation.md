# Cash on delivery

No pilot COD collection or reconciliation API was found. The app does not display customer collectable totals, accept an amount, or claim cash collected. COD support requires a backend event with an authoritative order amount, authenticated pilot assignment, idempotency key, discrepancy reporting, and later ledger reconciliation. UI-only amounts would not be authoritative.
