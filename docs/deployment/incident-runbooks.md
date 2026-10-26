# Incident runbooks

Every action needs an incident commander, ticket, timestamp and customer/financial impact record. Commands below are examples; substitute approved environment/context and inspect before write operations.

## Deploy / rollback
Prerequisite: reviewed immutable image digest, migration compatibility, health and approval. Deploy API/workers/web separately; check readiness, errors, queue age and order flow. Roll back application to prior digest if safe. Never reverse schema/data changes blindly; use forward fix.

## Migration
Check backup/PITR, current/head, reviewed SQL and lock plan; run one-shot migration job; verify history and smoke. Stop rollout on timeout/error; preserve logs and use reviewed forward repair.

## Redis or worker outage
Check provider health/network/TLS, preserve PostgreSQL outbox, restore worker, inspect oldest work and reconcile orders/payments before idempotent replay. Do not purge queue or replay all jobs without review.

## Stuck order / dispatch backlog
Identify state and durable event timestamps; verify merchant/pilot eligibility and current city pause; reconcile authoritative DB and event/outbox; use supported transition/reassignment with audit record. Do not edit rows directly or hide obligations.

## Payment exception / duplicate webhook
Check gateway reference, verified signature, idempotency inbox and ledger; hold uncertain case for finance. Never mark paid from client callback or resend refund without checking idempotency.

## City pause / pilot shortage
Pause new eligible intake; retain active order tracking; assign authorized operators; communicate and resolve outstanding orders/refunds/cash custody before resuming.

## DB saturation / customer incident / DR
Check pool metrics, slow query/provider events and worker concurrency; shed noncritical read load, do not scale blindly beyond DB budget. Page named owner/support, preserve evidence, invoke isolated restore plan only after incident approval. Escalation contacts and exact provider commands must be populated by the operator before launch.
