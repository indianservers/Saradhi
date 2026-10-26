# Redis and background workers

PostgreSQL is the durable transaction/outbox authority. Redis carries ARQ work and transient fan-out; do not treat a Redis queue acknowledgment as financial/order truth. API and ARQ worker are separate processes/deployments. Start with independent worker concurrency and resource limits; scale from measured queue age/depth and database budget.

Current code has retry limits and scheduled work, but durable dead-letter handling, poison-message isolation, queue-lag alerting, independently classified worker pools and outage recovery drills are not demonstrated. Confirm every handler is idempotent and safe after timeout/retry, persist failure context, bound retries/backoff and provide operator replay after inspection. Do not execute critical schedules only at API startup.

After Redis outage: verify managed cache health/auth/TLS; preserve PostgreSQL outbox state; restore worker connectivity; inspect queue and outbox age; re-enqueue idempotently; reconcile stuck orders/payments; do not bulk replay blindly. Worker restart and Redis-loss recovery tests remain release gates.
