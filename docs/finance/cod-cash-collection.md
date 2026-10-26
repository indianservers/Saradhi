# COD/COS cash collection

COD/COS cash collection is not implemented. Current delivery and order states do not represent cash collection, custody, handover, deposit, or reconciliation. Do not infer cash received from delivery completion or pilot earnings.

The required implementation needs an immutable amount obligation tied to a delivery/order/currency, pilot assignment ownership, idempotent collection confirmation, custody transfers and handover records, cash balance reads, discrepancy cases, finance reconciliation approvals, and balanced ledger postings. It must define single/multi-merchant allocation and how cash is split across delivery tasks before exposing a customer COD option.

The customer app currently offers the backend-reported online/sandbox option only. It does not claim COD is available.
