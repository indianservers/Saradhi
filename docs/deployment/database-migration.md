# PostgreSQL migration and release

Local PostgreSQL remains intact. The repository has a single Alembic history under `backend/migrations`; verify current/head and inspect generated SQL before changes. Never run reset/drop commands as deployment steps. Use separate runtime (DML only), migration (schema privileges), read-only reporting and backup roles. The runtime must not be superuser.

Migration rehearsal checklist: verify PostgreSQL/PostGIS versions and extension availability; validate migration history and schema; review SQL, lock duration and expand/contract compatibility; take provider snapshot/PITR point; migrate a staging-like sanitized dataset; compare row counts, checksums for selected stable data, sequences, indexes, FKs, migration version and financial ledger totals; run old/new API compatibility tests; record rollback/forward-fix owner. Export only approved encrypted data and destroy temp plaintext securely. No production data export or cloud migration was performed.

Use `alembic upgrade head` in a dedicated one-shot release job after approval, never API startup. A failed DDL may need forward repair; do not promise rollback for destructive or already-written changes. Keep old and new app versions compatible through rolling deployment. PgBouncer transaction mode is not yet validated against asyncpg prepared/session behavior.
