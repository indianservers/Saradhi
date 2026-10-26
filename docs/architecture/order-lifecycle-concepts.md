# Planned order lifecycle (not a relational model)

Customer cart is mutable intent and has no payment/settlement authority. A validated checkout
creates a parent order grouping the customer's purchase. Each merchant/branch receives an
independent child order, priced and accepted independently; one refusal need not invalidate
unrelated merchant fulfillment. Define partial acceptance/refund UX in Phase 2.

A child order can yield multiple fulfillment units (preparation, pickup, drop-off,
category-specific handling). Scheduled delivery tasks bind units to windows, time zones and
service-area policies. Tasks are distinct from rider assignments: assignments may be retried,
reallocated or cancelled without rewriting historical tasks. A parent can have several
merchant prep times, slots and pilots. Recurring subscriptions create dated occurrences,
not one permanently mutable order.

Payment transactions represent provider authorization/capture/refund events and reconciliation.
They do not stand in for ledger entries or merchant settlement transactions. Ledger obligations
must reconcile payment allocations, fees, commissions and refunds exactly. Settlements track
independent obligations, payout batches and provider reconciliation per merchant/pilot.

Plan explicit state machines, optimistic versioning, idempotency keys, aggregate invariants,
partial cancellation and compensation. External payment effects require durable workflows,
provider idempotency and reconciliation. Outbox -> broker -> idempotent consumer supports
merchant acceptance, payment confirmation, dispatch and delivery; no volatile scheduler may
act as payment/order authority. No tables or business records are created in Phase 1.
