# Backup and recovery

Proposed targets for business review only: RPO 15 minutes and RTO 4 hours. These are not achieved or proven. Select managed PostgreSQL automated backups/PITR and encrypted object versioning/retention after legal, cost and data-retention review. Define separate recovery owner and access.

No backup/restore drill was run in Phase 12; age/pg tools, credentials and disposable cloud target were unavailable. Never test by overwriting active Quickbuddy DB. Before production: create isolated disposable recovery DB/account, restore a backup/PITR point, validate Alembic history, extensions, row counts/checksums, foreign keys/indexes/sequences, ledger balance and sample orders, test app read-only, record elapsed RPO/RTO and securely destroy the isolated target. Protect backup keys separately from backups. Restore object files and verify references.

Do not export sensitive production records to unencrypted local files. Stop launch until a restore drill has passed and evidence is recorded.
