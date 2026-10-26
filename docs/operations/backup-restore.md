# Backup and restore runbook

## Scope and evidence

The local data directory `.local/postgres-data` is not a backup. `quickbuddy_dev` and
`quickbuddy_test` are separate loopback databases on port 5433. Their app roles cannot create
databases. PostgreSQL client utilities `pg_dump` and `pg_restore` were not available on PATH or
in the searched local installation paths, so this phase did not generate or restore an archive.
No backup success, RPO or RTO is claimed. The preexisting
`backups-and-restoration.md` describes managed-provider guidance; this runbook gives the safe
local procedure once matching PostgreSQL 17 client tools are installed.

## Local logical archive

Use a PostgreSQL 17 `pg_dump` client and an approved private destination with NTFS ACLs. Supply
password using an ACL-restricted `PGPASSFILE` or a short-lived process environment; never put it
on a command line or in shell history. Example with a protected passfile:

```powershell
$env:PGPASSFILE = 'C:\private\quickbuddy-pgpass'
pg_dump --host 127.0.0.1 --port 5433 --username quickbuddy_dev_owner `
  --dbname quickbuddy_dev --format=custom --no-owner --no-acl `
  --file 'C:\private\quickbuddy_dev_YYYYMMDD_HHMM.dump'
pg_restore --list 'C:\private\quickbuddy_dev_YYYYMMDD_HHMM.dump' | Out-Null
Remove-Item Env:PGPASSFILE
```

Choose a fresh, unique archive filename; verify it exists and is nonempty. Encrypt it at rest,
restrict readers, record checksum/size, and apply a reviewed retention policy. Never commit
archives or passfiles. Archive the test database separately if test evidence needs to be kept.

## Isolated restore drill

Provision a new empty disposable database with an approved local database-owner/operator
credential. Check the exact target name and ensure it does not exist first. Restore without
`--clean`, `--create` or overwrite options:

```powershell
createdb --host 127.0.0.1 --port 5433 --username quickbuddy_local_admin quickbuddy_restore_YYYYMMDD
pg_restore --host 127.0.0.1 --port 5433 --username quickbuddy_local_admin `
  --dbname quickbuddy_restore_YYYYMMDD --exit-on-error --no-owner --no-acl `
  'C:\private\quickbuddy_dev_YYYYMMDD_HHMM.dump'
```

Validate Alembic revision, schema/table and constraint counts, representative row counts,
financial balance and immutable journal checks, outbox/inbox state, app readiness, and a set of
read-only representative requests. Record elapsed time and archive/checksum identity. Keep the
restored DB until the drill is reviewed; any disposal must be an explicit action against that
unique temporary DB only. Never point a restore command at `quickbuddy_dev`, `quickbuddy_test`,
production, or an unspecified database.

Managed PostgreSQL production readiness includes automatic backup/PITR, encryption, region and
retention policy, documented incident owner, and a scheduled restore drill with agreed RPO/RTO.
