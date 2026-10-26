# Financial integrity and reconciliation

All exercised payments used isolated fixtures and the explicit sandbox or injected fake provider. No Razorpay credentials were requested; no real transaction or payout occurred.

## Existing tested invariants

- Ledger posting validates account organization/book/currency, currency precision, one book per journal, and balanced signed lines; database deferred validation and immutable posted records are present.
- Reversals create a new reversing journal rather than editing posted lines.
- Sandbox webhook idempotency and repeated partial refund produce a single logical refund in integration tests.
- Razorpay adapter tests cover signature verification; fake-provider integration verifies server-derived amount, capture state, webhook dedupe, invalid signature, unmatched event, and late event handling.
- Refunds require a matching separately approved request, organization scope, amount limit, confirmed payment, and idempotency key.

The exercised fixture scenarios had no unexplained discrepancy. This does not establish complete COS/COD cash custody, tax, pilot earnings vs customer cash, multi-merchant allocation, settlement payout, refund reversal, or production gateway reconciliation. These are open release blockers. Financial regression suite: `.venv\Scripts\python.exe -m pytest tests/integration/test_vertical_slice.py tests/integration/test_razorpay_webhook.py tests/integration/test_finance_approval_queue.py -q`.
