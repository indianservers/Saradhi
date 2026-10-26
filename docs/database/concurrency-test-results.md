# Concurrency and transaction test results

The real PostgreSQL integration suite ran against `quickbuddy_test`, using the in-process ASGI
HTTP transport and separate authenticated sessions. Latest full run: 23 tests passed in 41.33s
(`../operations/phase-2a-tests.xml`). It includes 30-occurrence recurrence dedupe, distinct
address grouping, multi-merchant payment rejection and the leased outbox claim checks.

The committed concurrency evidence records a 100-request checkout test on one branch/shared
stock row: 100 independently authenticated customers, 100 HTTP 201 results, 2.914 seconds
(34.313 confirmations/second) with pool size 5 and max overflow 10. This is an in-process local
correctness/load sample, not a sustained throughput, provider, network, GPS or delivery-capacity
benchmark. A separate scarce-stock race admitted one of two confirmations, returned 409 for the
other, and retained one reserved unit. Partial unique assignment constraints and a concurrent
pilot offer race ensure only one offer wins a task.

Checkout locks resources in stable order, checks stock/capacity in conditional SQL updates,
records idempotent movements and outbox events transactionally, and releases failed writes
before HTTP success. Each request owns its session. Database timeouts bound statements, locks
and idle transactions. Outbox claims commit before publisher I/O; delivery is at least once and
consumers must deduplicate by event ID. The relay has bounded retries and dead letters after
eight failed attempts. Tests verify the publisher can obtain NOWAIT row access while publishing,
retry/dead-letter behavior, inbox rollback and deduplication.

Evidence: `../operations/concurrency-evidence.json`, integration tests under
`../../tests/integration`, and the complete run output from this turn (21 passed, followed by
three targeted passes). No throughput SLO or RPO/RTO is inferred from these tests.
