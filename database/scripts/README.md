# Dedicated development database setup

No database was created: authorized credentials were not supplied. No secrets from other projects
were read. No database names, data or service configuration were changed.

Ask the database owner for a dedicated least-privilege role and authorized administrative
connection. Owner action: query pg_database using parameterized name quickbuddy_dev; if absent,
create database quickbuddy_dev owned by the approved role. If present, confirm ownership and
purpose before use; never drop or overwrite it. CREATE DATABASE must run outside a transaction.
Do not execute unattended scripts against another project's cluster without owner approval.

Database owner's inspection SQL (using an explicitly authorized administrative session):
`SELECT datname FROM pg_database WHERE datname = 'quickbuddy_dev';`
Only if no row exists, and after approving a dedicated owner role, run
`CREATE DATABASE quickbuddy_dev OWNER <approved_role>;` with the actual role identifier.
Do not execute the angle-bracket template literally. Role creation and credentials are
the cluster owner's responsibility; no default password or public registration is supplied.

Set DATABASE_URL=postgresql+asyncpg://<approved-role>:<percent-encoded-password>@127.0.0.1:5432/quickbuddy_dev
in ignored root .env. Run `./tools/dev.ps1 database`. It only reads SELECT version(),
current_database(), and available extension metadata. Candidate future extensions: postgis,
pg_trgm, btree_gist, pgcrypto (not required/installed automatically in Phase 1).
Use backend/migrations only. Never run schema creation or application migrations against an
unrelated database. Validate TLS requirements with the database owner before remote access.
