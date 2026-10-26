# Event delivery and recovery

Critical checkout, stock, merchant acceptance, payment, assignment, pickup, delivery and refund
operations write integration.outbox_events in the same database transaction as their effects.
Envelopes contain a UUID, event type, payload version, aggregate UUID, correlation ID and minimal
JSON payload. Database guards prevent rewriting identity/type/payload/version or deleting events
without controlled archival. Mutable attempts/available_at/delivered_at/dead_lettered_at are delivery
state. No process-local queue is financial or order authority.

EventPublisher is a provider-neutral asynchronous interface. relay_batch claims bounded due rows
with FOR UPDATE SKIP LOCKED, publishes with the stable event ID, then marks delivered. A crash
after publication but before commit can redeliver; transport/consumers must be idempotent. Eight
attempts lead to persisted dead-letter state, with bounded exponential delay plus jitter.
Production adapters must enforce publish timeout and consider lease-based claims instead of
holding locks during network calls. No external broker is configured or falsely reported working.

consume inserts a unique (consumer,event_id) inbox marker and invokes the handler within the
caller transaction. Handler failure rolls back marker and local effects; retries can safely run.
External side effects need provider idempotency or another outbox. This is not an exactly-once
external processing claim. Payload contracts are versioned; reject unknown versions deliberately.

The local PostgreSQL database worker persists an in-app notification job for order.created,
commits its inbox receipt and marks internal handoff atomically. That delivered_at is an internal
handoff, not proof of SMS/email/push delivery. Unknown event types remain pending for configured
handlers; they are not dropped. The worker also expires stock reservations and prunes bounded
expired GPS/proof/rate-bucket records. Its poll interval is not authoritative scheduling state.
Redis/ARQ remains an optional prepared demo queue and is unavailable locally.

Recovery: diagnose backlog by oldest available_at and attempts; repair the downstream dependency;
use a privileged reviewed transaction to clear dead_lettered_at and reschedule available_at for
specific event IDs. Preserve envelope and inbox state; do not reset all consumers or delete events.
Publish stable IDs on replay. Audit operational recovery. Archive delivered events only after
consumer retention/replay requirements and referential references have been reviewed.
