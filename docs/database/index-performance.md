# Index and query-plan audit

The catalog has 695 indexes, including primary/unique backing indexes, and the audit found no
invalid index. PostgreSQL `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` ran for owned orders, stock,
latest pilot location, due outbox rows, order items per merchant order, support tickets per
organization and pilot assignments per pilot. Full plans and timings are in
`../operations/phase-2-database-evidence.json`; samples are tiny integration fixtures and must
not be extrapolated to production distributions.

Observed expected access paths include `ix_orders_user_id`, `ix_stock_balances_branch_id`,
`uq_pilot_latest_location_pilot_id`, `ix_outbox_pending` and
`ix_order_items_merchant_order_id`. The claimable outbox partial index supplements the due-event
index for leases. PostgreSQL may choose sequential scans on small reference tables; that is
reasonable at this fixture size. Do not add blanket indexes to every FK: they consume storage
and increase write cost. Recheck support queue, assignment history and other FK access paths
against production query frequency and realistic cardinality before adding targeted indexes.

Plans showed sub-millisecond execution on cached small local tables, which is only a smoke-level
observation. No 10K+ row benchmark, sustained load, cold-cache run, `pg_stat_statements` review,
write amplification measurement or production-like `ANALYZE` distribution was performed.
Capacity and production latency remain unknown. Record representative query latency, rows,
buffers, write rate and `pg_stat_user_indexes` before tuning or partitioning.
