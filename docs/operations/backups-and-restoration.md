# Backups, restoration and managed migration readiness

The local isolated cluster is .local/postgres-data, not a backup. Keep .env/.secrets separately
protected; neither belongs in version control or public artifacts. Development/test roles are
separate non-superusers and cannot create databases. Production needs separate migration-owner,
runtime DML and read/report roles, external secret injection and verified TLS.

Use the same-major pg_dump client with a restricted PostgreSQL service/passfile or an injected
credential environment, never plaintext password arguments or terminal output. A local logical
backup command is `pg_dump -h 127.0.0.1 -p 5433 -U quickbuddy_dev_owner -d quickbuddy_dev -Fc -f <private-backup-path>`.
The interactive/passfile authentication must be supplied securely. Encrypt backup objects,
restrict retention/access and test restores. No pg_dump or destructive restore was executed
as part of this phase. Backup/restore command paths are examples, not evidence of a restored backup.

Restore into a NEW explicitly named isolated database using pg_restore; verify schema revision,
row counts, ledger balance, outbox/inbox consistency and application checks before any cutover.
Never use --clean or reset a development/production database by default. An actual recovery drill
and agreed RPO/RTO are launch gates. Managed PostgreSQL should enable supported automatic backups
and PITR; validate region, residency, extension support, connection limits and restore procedures.

Future AWS RDS/DigitalOcean migration: pin PostgreSQL/extension versions, verify ordinary SQL
compatibility and PostGIS availability, provision private networking and TLS, test logical copy
and migration replay in staging, pause/control writes for cutover, reconcile totals/queues and
retain rollback evidence. Alembic runs once per release, never on each API replica's startup.
No cloud services, gateways, production credentials or provider-specific schema were provisioned.
