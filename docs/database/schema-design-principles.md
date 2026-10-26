# Phase 2 schema design gates

No business tables or initial schema revision exists yet. backend/migrations is the ONLY
executable Alembic source. database/migrations and database/design are reference/design
locations; they must never form another migration history. Alembic has no pending revisions.

Design tenant and geographic scope, branch/category extensibility and indexed ownership
predicates. Decide aggregate IDs, foreign keys, constraints, state transitions and concurrency
control from reviewed order lifecycle. Use timestamptz/UTC for instants and IANA timezones for
schedules. Exact Decimal/integer minor-unit money with ISO currency and explicit scale/rounding.
Never use floats for balances, commissions, fees, payments or settlement calculations.

Plan balanced append-only ledger, reconciled allocations and settlement obligations;
outbox/inbox/idempotency in the same durable transaction as corresponding effects. Decide
idempotency retention, TTL and request fingerprint behavior; Redis is only auxiliary.
Capture audit actor/action/resource with restricted retention and redact sensitive payloads.

Consider PostGIS GiST indexes, pg_trgm catalog search and btree_gist exclusion constraints
only when required by actual queries. Required now: base PostgreSQL with transactional DDL.
Extensions are optional future candidates; availability/install versions remain unverified.
Partition high-volume GPS/audit by retention/region only after workload evidence. No premature
partitioning of low-volume transactional tables. Document PII classification, residency,
backup/PITR objectives, deletion policy, index budgets and migration rollback/forward repair.

Use naming convention metadata in backend/shared/database.py; revisions named YYYYMMDD_<rev>_<slug>.
Review generated migrations, test upgrade from empty and previous snapshots and inspect locks.
Never create metadata automatically on API startup. Migration credentials must be separate
from runtime DML roles in production. Sessions commit only after successful use cases and
rollback on errors; keep external network calls outside database transactions.
