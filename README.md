# Quickbuddy

A six-application hyperlocal platform with one shared FastAPI modular backend. Phase 2 now
includes a real PostgreSQL schema, scoped password/session authentication, multi-merchant
checkout, stock/batch reservations, merchant preparation, pilot/recipient workflows, guarded
ledger posting and transactional outbox/inbox infrastructure.

Start with [DEVELOPMENT.md](DEVELOPMENT.md), [Phase 2 results](docs/operations/phase-2-validation.md),
[API reference](docs/api/api-reference.md) and [database architecture](docs/database/enterprise-schema.md).
The Phase 1 validation report is historical. Flutter SDK, PostGIS and Redis limitations remain
explicit. No cloud deployment or production gateway is configured and frontend screens were not
expanded in Phase 2. The application shells and generated shared TypeScript client are preserved.

Local PostgreSQL 17.11 runs in the user-approved isolated .local cluster on 127.0.0.1:5433;
quickbuddy_dev and quickbuddy_test have separate non-superuser owners. Existing port 5432 was
not altered. Secrets and data are ignored, Windows ACL-restricted local files. There is no
default administrator account. Business fixtures exist only in the dedicated test database.

Use tools/dev.ps1 for migrations, API, tests, lint and contracts. Source, migrations and docs
are project artifacts; .env, .secrets and .local must not be committed or copied into images.
