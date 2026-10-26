# Data job recovery

Job owner may use `GET /api/v1/bulk/imports/{id}`, `GET /api/v1/bulk/imports/{id}/errors`, and `GET /api/v1/bulk/jobs`. Upload retry with the same actor, idempotency key and exact file hash returns the same job. Same key with different content returns conflict. External refs protect commit retries across distinct jobs.

Only an unpreviewed `VALIDATED` job can be cancelled. Commit requires preview and is one bounded transaction; repeat commit of a completed/partial job returns the saved result without re-creating rows. A DB transaction failure rolls back that commit. Row conflicts are reported; do not edit job rows directly.

No worker crash/resume, stuck-job reaper, immutable event stream, file retention purge, operator retry or DLQ exists yet. The implemented work is synchronous, so these runbooks do not imply async job processing. Investigate by job ID using the owner-scoped API, preserve audit IDs, fix the source file and submit a new idempotent operation.
