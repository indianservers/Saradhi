# Phase 2.A final review

## Completed and verified

- Audited both named local databases on PostgreSQL 17.11 and applied additive Alembic revision
  `20261026_0007` to `quickbuddy_dev` and `quickbuddy_test`. No reset, drop, downgrade or
  development fixture seeding occurred.
- The 247-table/1,661-column catalog matches ORM metadata in both databases. No invalid indexes,
  unvalidated constraints or timezone column mismatches were found. All 247 tables and 796
  constraints are present; 695 indexes and 58 non-internal triggers are cataloged.
- Real PostgreSQL HTTP integration suite passed 23 tests in 41.33s after updating the migration
  smoke expectation. This full run includes recurring schedules, address grouping,
  multi-merchant payment rejection, and leased outbox tests.
- Added durable outbox leases: claim and commit before network I/O, bounded retries, expiry
  recovery, safe dead-lettering and idempotent consumer expectation. Added test for no row lock
  during publishing. At-least-once delivery still requires downstream deduplication.
- Verified 100 concurrent confirmations/2.914 seconds on a local in-process test, along with
  scarce-stock rejection, authorization, journal integrity, sandbox webhook/refund and
  idempotency scenarios.
- Added read-only schema audit tooling and focused audit/runbook documentation.

## Launch gates / unsupported claims

- No matching `pg_dump`/`pg_restore` client utilities were found; no archive or isolated restore
  drill was executed. Obtain the PostgreSQL 17 client tools, create a protected archive and test
  a restore into a new isolated DB before production.
- PostGIS is unavailable in the local PostgreSQL build. Courier geospatial serviceability remains
  fail-closed. Obtain a compatible extension or select a managed service supporting it; validate
  migration, boundaries, distance, capacity and plans.
- Production payment provider, multi-merchant revised allocations/refunds/settlement, automatic
  ledger posting/reconciliation, delivery routing and real pilot capacity are not proven.
- The configured database worker does not run the broker outbox relay; a durable publisher,
  worker supervision, timeout-vs-lease policy, metrics/alerts and dead-letter operations need a
  deployment integration before external event delivery is claimed operational.
- No RLS policies, cloud deployment, sustained 10K+ row plans, public-network load benchmark,
  formally defined RPO/RTO or production authorization penetration test were completed.

## Evidence

Catalog evidence: `../operations/phase-2-database-evidence.json` and
`../operations/phase-2a-schema-evidence.json`. Concurrency sample:
`../operations/concurrency-evidence.json`. Operational guidance:
`../operations/backup-restore.md`, `../deployment/postgres-cloud-readiness.md`, and
`../database/postgis-requirements.md`.
