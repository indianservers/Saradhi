# PostgreSQL integrity assessment

Inventory observed 259 SQLAlchemy tables across 13 schemas, 198 foundation model registrations, and 19 Alembic version files. Local test configuration explicitly refuses a database other than loopback `quickbuddy_test`; the full PostgreSQL integration suite migrated and passed (95 tests).

Reviewed controls include named PK/FK/unique/check constraints, migration-managed indexes, organization/branch scoping triggers, immutable record triggers for financial/history/audit data, `NUMERIC` amounts, UTC connection timezone, 10-second statement timeout, 5-second lock timeout, 30-second idle transaction timeout, row locking in checkout/dispatch/refund flows, idempotency records, and deferred journal balance validation.

Evidence includes real DB checkout concurrency (100 requests, exactly 100 expected logical orders for available 100 stock), pilot assignment exclusivity integration scenarios, idempotent sandbox refund/webhook, recurring occurrence deduplication, stock and order invariants, and Alembic upgrade in integration setup.

Not verified: every table/nullable/constraint against a production catalog; orphan sweep against production-like data; 200 buyers vs 20 stock; 50-way dispatch acceptance; 20-way refund; concurrent merchant transitions; COD retries; settlement posting races; lock-wait/deadlock telemetry; EXPLAIN ANALYZE on representative data; autovacuum and retention at scale. No production data was queried or modified. No destructive migration was added in this phase.
