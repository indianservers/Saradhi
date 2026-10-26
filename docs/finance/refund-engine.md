# Refund engine

Existing refund approval is a separately audited maker-checker workflow with no self-approval, organization scope, and a database guard requiring a matching approved request. The current executable refund route is sandbox-only. Its immutable refund records and payment-level refunded counter are not yet connected to Razorpay asynchronous refund processing.

Razorpay adapter includes a refund request primitive, but no production refund route calls it. Refund events are authenticated and retained in the webhook inbox with `refund_workflow_unavailable`; they do not change financial balances. Do not issue external refunds through an ad hoc script.

The required next step is an idempotent refund request/status model, allocation-level refundable balance, provider reference correlation, webhook-driven completion/failure, and balanced immutable refund/reversal postings. An HTTP submission response must remain pending until provider-confirmed status.
