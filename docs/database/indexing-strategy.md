# Indexing and query-plan evidence

The live catalogs contain 694 indexes, of which 345 are explicit ORM indexes; the rest back
primary/unique constraints. Most supplemental tables index their FK columns. This is an
initial integrity/read foundation, not evidence that every index is useful at production scale.
Review pg_stat_user_indexes and write amplification before retaining redundant indexes at scale.

Core access paths: owned orders by user_id plus UUID cursor; branch/variant stock uniqueness;
branch/variant/time prices; cart_id item lookups; merchant order parent/branch lookups;
exclusive partial task-assignment index; session/user and refresh-digest uniqueness;
organization/idempotency journal uniqueness; outbox partial available_at index; audit
organization/time/id; latest pilot location unique pilot_id; history pilot/time/id and
history/proof expires_at/id retention indexes. No request scans GPS history for current location.

Quote reads join item/product/variant/branch/window once and batch address, price, currency,
availability and tax lookups. Serviceability is cached within one quote per distinct branch,
window, method, destination and category. Writes still flush per item/reservation/event; this
is a known optimization target after measured realistic fanout, not a hidden capacity claim.

backend.scripts.database_report actually executes EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
for owned order pagination, stock lookup, latest pilot location and due outbox queries on
quickbuddy_test. See ../operations/phase-2-database-evidence.json for complete plans. Small
fixture tables may legitimately choose sequential scans. These plans are not substitutes for
large historical datasets, realistic distribution, ANALYZE statistics and slow-query evidence.
The report also records pool status and verifies that local owners are not superusers.

All API collection limits are bounded 1..100 and cursors encode UUID ordering. Sorting is
fixed/allowlisted; arbitrary SQL order/filter fragments are never accepted. Page cursors do
not provide a stable snapshot across concurrent inserts. Use export/read-model mechanisms
for point-in-time reporting. Current collection order is UUID order, not creation-time order.

Add production indexes concurrently in separate reviewed non-transactional deployment steps
when tables become large; the current migrations run transactionally on a new schema.
Keep managed-provider extension capabilities and connection budgets explicit. Partition GPS,
audit or outbox history only after retention/volume evidence; global uniqueness and FK rules
across partitions must be designed first. Do not partition every operational table.
