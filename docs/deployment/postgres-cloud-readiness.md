# PostgreSQL cloud readiness

The application uses PostgreSQL 17-compatible SQLAlchemy/Alembic and was audited on a local
PostgreSQL 17.11 cluster. Development and test DB roles are non-superusers and each is confined
to a named loopback database. Migrations are explicit, additive and run with the guarded project
command; production must run them once per release as a controlled job. API replicas must not
perform startup migrations.

Before selecting RDS, DigitalOcean or another managed service, verify PostgreSQL major/version,
extensions, private networking, TLS certificate validation, region/residency, max connections,
pool budget, statement/lock timeouts, backup/PITR, restore workflow and monitoring. PostGIS is a
required capability for courier serviceability and is absent locally. The candidate provider and
deployment architecture in `cloud-portability.md` are planning notes, not a provisioned target.

Production role plan: separately controlled migration owner, least-privilege API DML role,
worker role, read/report role and operator identity. Inject secrets through a managed secret
service; never ship `.env`, signing material, DB credentials or local backups. Enforce TLS,
network allowlists/private endpoints, managed encrypted backups and tested restore. Set pool
size/overflow so all replicas and worker processes stay within reserved connection capacity.

Forward-only migrations have no automatic downgrade. Prepare reviewed repair migrations, test
upgrade on a restored staging copy, verify indexes/constraints, and retain rollback/cutover
plans. No cloud DB, cloud credentials, network route, provider extension or production load test
was used in this phase. Backup utility absence also prevented a restore drill, which remains a
readiness gate.
