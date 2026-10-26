# Enterprise schema — Phase 2

247 real tables across identity, geo, merchant, catalog, inventory, commerce, fulfillment,
finance, engagement, operations, intelligence, integration and audit. These schemas are
installed in both local quickbuddy_dev and quickbuddy_test. Actual catalog evidence is in
../operations/phase-2-database-evidence.json; machine-readable column/relationship definitions
are in schema.json and the complete human dictionary is data-dictionary.md.

The local PostgreSQL 17.11 binaries were reused after explicit user approval to create an
isolated cluster in .local/postgres-data on loopback port 5433. The unrelated server on 5432
was not altered. Database owners are separate NOSUPERUSER/NOCREATEDB/NOCREATEROLE roles.
Credentials and RSA keys are ignored and restricted to the current Windows account by ACL.
No default customer or administrator account was created in development.

Core typed SQLAlchemy models live in backend/persistence/models.py. Supplemental relational
foundations live in foundations.py and are mapped into the same registry. These are actual
FK-bearing typed tables, not EAV bags. Only scoped operational services have public adapters;
there are no generic CRUD endpoints for every table. Pure domain rules never import FastAPI
or SQLAlchemy. Application services coordinate contexts; repositories do not leak to clients.

Identifiers use UUIDv4 because Python 3.12 does not supply a native UUIDv7 implementation.
Absolute times use timestamptz, connections use UTC, and geography/schedules use explicit
IANA zones. Monetary columns use numeric(20,4), currencies declare a scale 0..4, and all
business arithmetic uses Decimal with ROUND_HALF_EVEN. No float or PostgreSQL money column.
Historical order items, stock movements, posted journals/lines, audit and immutable events
are protected with database triggers rather than soft deletion. Mutable state uses explicit
statuses, expected versions, row locks and state histories.

Migrations are the sole authority: 20261026_0001 enterprise DDL/guards; 0002 permission masters;
0003 separate refund approvals and ledger identity guards; 0004 FEFO allocations/batch movements;
0005 history/retention indexes. The initial revision contains a frozen JSON DDL snapshot and
0004 contains a frozen table SQL artifact. Runtime metadata.create_all is never used.
Downgrades deliberately refuse destructive removal; use reviewed forward repair or restore.
Alembic check reports no model/schema differences after all five revisions.

The database has 793 constraints (792 ordinary ORM constraints plus one deferred ledger
constraint trigger), 694 indexes including PK/unique backing indexes (345 explicitly modeled
indexes), and 57 user triggers. No table is prematurely partitioned. All FKs use RESTRICT;
retention explicitly targets ephemeral records without cascading financial deletion.

PostGIS is absent from this distribution. No extension was silently installed and no radius
or polygon approximation was substituted. Pickup functionality works; courier serviceability
returns a typed spatial_unavailable 503 until an approved PostGIS installation, reviewed spatial
Alembic revision and valid service-area policies exist. See postgis-requirements.md.

Model/repository foundation does not mean complete business behavior: pricing options, tax
calculation, final weighing, regulatory approvals, production gateways/payouts, full recurring
order revalidation, provider notifications and external broker transport remain integration work.
Unsupported checkout cases fail explicitly instead of calculating unsafe amounts.
