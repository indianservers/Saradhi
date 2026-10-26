# Finance approval controls

The company console now lists refund approval requests for an organization returned by `/api/v1/finance/authorized-organizations`. List access requires database-backed `finance.read` scope, emits read audit records, and supports a bounded cursor page. The proxy permits only the authorized-organizations and refund-approvals reads plus the decision route.

Approval/rejection requires a reason and `finance.write` scope. The backend rejects self-approval, locks and checks pending state, writes an immutable decision record, and audits the outcome. An approved request is a control record; it does not itself execute a refund. Refund execution remains a separate finance flow. Ledger summaries, reconciliation, settlement reporting, and multi-currency rollups are not included.
