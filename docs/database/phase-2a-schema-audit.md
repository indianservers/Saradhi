# Phase 2.A schema audit

Audit run 26 October 2026 against the configured loopback PostgreSQL cluster on port 5433.
Both databases were explicitly checked by name (`quickbuddy_dev`, `quickbuddy_test`); neither
the unrelated 5432 instance nor any cloud database was contacted. PostgreSQL reports version
17.11. Both database roles are non-superusers. Both schemas are at Alembic revision
`20261026_0007` after applying the additive outbox lease migration.

Each database contains 247 tables across identity, geo, merchant, catalog, inventory, commerce,
fulfillment, finance, engagement, operations, intelligence, integration and audit. The schema
has 1,661 columns and matches registered SQLAlchemy metadata: no missing or extra tables or
columns, no timezone type mismatches, no constraint-count differences, no invalid indexes and
no unvalidated constraints. The outbox lease-pair check is migration-managed (not ORM metadata)
and separately verified as validated. There are 796 constraints, 695 indexes including
constraint indexes, and 58 non-internal triggers. See machine evidence in
`../operations/phase-2-database-evidence.json` and `../operations/phase-2a-schema-evidence.json`.

All modeled foreign keys are installed and validated, so PostgreSQL prevents orphan references
on future writes. The application has explicit RESTRICT semantics for financial and historical
references. This audit compared catalog definitions and did not scan production-sized data for
orphan rows; only the synthetic test database was written by tests. Core amounts and quantities
use Numeric/Decimal; timestamps use timezone-aware PostgreSQL types and connections set UTC.

Optional extensions available from this Windows distribution include `btree_gist`, `pg_trgm`
and `pgcrypto`; none is installed. PostGIS is unavailable. Consequently, courier polygon and
distance serviceability cannot be validated or enabled locally; courier quote paths fail closed.
Do not approximate spatial policy with coordinate math.

The configured app roles cannot create/drop databases or act as superuser. Migrations were
applied using the guarded project command only to the two named loopback databases. No reset,
drop, downgrade, fixture seeding or deletion was run against development. All test fixture data
is synthetic and belongs to `quickbuddy_test`.

Re-run with `python -m backend.scripts.phase2a_schema_audit` and
`python -m backend.scripts.database_report`. Both commands restrict inspection to the two local
Quickbuddy databases and omit credential strings and row-level personal data.
