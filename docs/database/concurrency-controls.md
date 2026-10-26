# Transactions, concurrency and retries

Every HTTP operation receives a distinct AsyncSession. No session is shared across concurrent
tasks. Write dependencies use function-scoped FastAPI Depends so the transaction commits before
the response is sent. Failure rolls back aggregate state, stock, slots, idempotency and outbox.
Authentication rate counters and refresh-reuse revocations use explicit committed transactions
before a 401/429 response, so errors do not erase the protection they triggered.

Checkout: unique (user_id,key), fingerprint comparison and ON CONFLICT serialization; quote/cart
row locks and expected cart version; stock rows locked in sorted branch/variant order; atomic
UPDATE ... WHERE on_hand-reserved>=quantity; CHECK 0<=reserved<=on_hand; slots reserve with
UPDATE ... WHERE reserved+count<=capacity. Reservations have one order item and idempotent
reserve/release/deduct movement keys. Row locks prevent double release/expiry/acceptance.
Batch stock uses FEFO locks and persisted per-reservation allocations, excludes stock expiring
before the local delivery date and releases or consumes batch reservations with aggregate stock.

Assignments: task row lock, consistent task-before-assignment locking and a partial UNIQUE
index on task_id for offered/accepted/picked_up assignments. A second offer/accept cannot win
an exclusive task. Expected task version protects pickup/failure/acknowledgment. Offer expiry
is checked against persisted timestamps; a new offer can expire a stale one under the lock.

Ledger: organization-level serialization plus journal idempotency, book/account scope FKs,
header locking and deferred database balance constraints. Refunds serialize on payment and
approval records with cumulative amount checks and separate decision actor. Coupons serialize
on order then coupon and enforce total/user/merchant limits and stacking. Internal coupon
entitlement consumption is not an API that silently reprices a confirmed order.

Outbox workers claim bounded batches using FOR UPDATE SKIP LOCKED. Inbox deduplication and
handler effects commit together. External delivery is at least once, never exactly once.
Production transport needs short publish timeouts/leases so broker latency cannot hold a DB
transaction indefinitely. The current local database worker handles in-app notification handoff,
reservation expiry and bounded retention without Redis. It does not execute payment workflows.

Connections set statement_timeout=10s, lock_timeout=5s and idle_in_transaction_session_timeout=30s;
driver command timeout is 15s and pool timeout 5s. Defaults are 5 pooled + 10 overflow per API
process. Budget replicas/workers/admin reserve against max_connections before scaling. Deadlock
40P01 and serialization 40001 become typed retryable 409s; retry the entire transaction with the
same business idempotency key and bounded jitter. Do not blindly retry an external charge.

Actual evidence: tests use real PostgreSQL on quickbuddy_test, including final-unit overselling,
exclusive offers, repeated checkout/refund/webhook/consumer operations and a 100-request concurrent
checkout workload with 100 independently authenticated sessions. See ../operations/concurrency-evidence.json.
This is a short in-process ASGI/database correctness test, not a sustained full-system capacity claim.
