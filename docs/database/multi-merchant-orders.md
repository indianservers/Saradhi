# Multi-merchant orders and delivery separation

A mutable cart belongs to one global user. Cart lines reference one branch, variant, quantity,
delivery window, fulfillment method and optional owned destination. One cart can contain
several merchants, windows and addresses. A quote snapshots product/variant names, unit,
quantity, price/book reference, branch, currency, addons/discount/tax components and address.
No future catalog update rewrites a confirmed order item. Options, regulated products,
variable final weights or configured tax products without approved calculators are rejected.
Mixed currencies must be separate checkouts; no floating-point financial arithmetic.

Confirmation locks user/key idempotency, quote and cart; validates version/expiry/ownership;
revalidates branch status/hours/closures, prices, method, destination and capacity; locks stock
in stable order; atomically reserves slots and sellable stock; writes parent, merchant children,
fulfillment units, tasks, immutable item snapshots, history and outbox events in one transaction.
A retry returns the original parent; another quote with the same key conflicts.

Exactly one merchant order exists per branch for a given checkout. Fulfillment units split
that child's items by window, delivery method and destination, and each unit has a delivery
task. Order items explicitly reference their fulfillment unit. Preparation/acceptance is not
pilot assignment. A child can be accepted/preparing/ready while another is rejected; independent
stock and slot reservations are released for rejected unpaid children. Parent totals remain
historical quoted obligations and are not silently reduced by a child status edit.

Merchant transition: pending -> accepted or rejected; accepted -> preparing (cancellation
requires explicit stock-return validation); preparing -> ready; fulfillment completion -> fulfilled.
Expected versions and row locks protect each transition. Acceptance confirms/deducts inventory.
Expired reservations cannot be accepted. Customer cancellation is supported only for unpaid,
unaccepted parent orders and releases all reservations/capacity. Already confirmed payments
require separately approved allocated refund processing; paid edits and substitutions are
blocked until that financial workflow is implemented. No arbitrary status PATCH endpoint.

Courier task flow is unassigned -> offered -> assigned -> picked_up -> delivered, with failed
states and offer expiry. Pickup by customer uses recipient acknowledgment directly once ready.
A recipient acknowledgment is performed by the actual order owner, not the pilot or merchant.
Proof references are private and expire after 30 days. One pilot can hold several tasks; the
current deterministic strategy selects an available verified pilot in the branch city by UUID.
Advanced route/capability/vehicle batching remains a dispatch integration requirement.

Group/corporate membership, scheduled order and recurrence tables exist, but their complete
end-user orchestration is not public API functionality yet. Daily/weekly/monthly/business-day
recurrence expansion is persisted/idempotent, explicitly handles exceptions and rejects DST
fold/gap ambiguity. Monthly missing dates are skipped. Occurrences await merchant/stock/price/
payment revalidation; generation never automatically charges a customer or creates an unsafe order.
