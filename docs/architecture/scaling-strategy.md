# Capacity assumptions, measured limits and future benchmarking

10,000 orders/day divided by 86,400 = 0.11574 order/s averaged across 24 hours. Plan at least
10x = 1.1574 order/s, configurable 50x = 5.787/s peaks and 100x = 11.574/s bursts. Scale the
model to 100,000+/day only after evidence. Orders are not equivalent to requests or GPS events.
Assume 30 API calls/order plus browsing (2,000 users / 10s = 200 rps), pilot telemetry
(1,000 pilots / 5s = 200 events/s), merchant fanout, callbacks and retries. Parameterize each.

Phase 2 actually runs a correctness workload with 100 independently authenticated customers
confirming checkout concurrently against one shared stock row and a 100-capacity window on
real quickbuddy_test. Every request must return 201; final reserved stock/capacity must be 100.
Exact latest results, timing, pool configuration and limitations are in
../operations/concurrency-evidence.json. It uses in-process ASGI, not a deployed network or
provider, and covers confirmation only. It is not proof of full-system 10,000/day capacity.

The k6 checkout.js harness prepares 10x average, configurable peak and burst arrival profiles
with up to 1,000 VUs. It requires a dedicated test API header, an actual test token, prepared
stock/window/product IDs and a unique run ID; it refuses non-test APIs. k6 is unavailable
locally, so this sustained network/load scenario has not been executed. health.js remains only
a process liveness benchmark. The test server command is `python -m backend.scripts.serve_test_api`.

Future protocol: name CPU/RAM/disk/network, create representative tenant/product/order history,
warm up 5min; average 15min; 10x 30min; 50x 15min; 100x 2min bursts; 4h soak. Mix browsing,
merchant preparation, multiple branches/addresses, scheduled release bursts, GPS batches,
payment callback retries and durable outbox backlogs. Test restart/recovery, slow providers,
Redis outage, duplicate consumers, pool pressure, deadlocks and backlog drain. Correctness of
money, inventory and exclusive assignment takes precedence over latency.

Provisional review targets: non-provider p95<300ms/p99<1s, order commit p95<750ms, error<1%,
steady queue lag<5s. Record distributions rather than dividing daily orders into an average.
Capture pool waits, lock waits, DB CPU/IO, rows examined, statement timeouts and write amplification.
Read-only EXPLAIN ANALYZE evidence exists for fixture-scale queries in the database report.

Pool budget: replicas*(5 pooled+10 overflow) + worker/migration/admin reserve, with max_connections
100 in this small local cluster. Do not add replicas or 1,000 concurrent DB sessions blindly.
Each API request gets its own AsyncSession; current-location upsert uses pooled connections,
not a connection per GPS event. Latest-location reads avoid historical scans. Add microbatch
telemetry ingestion after measuring requirements and preserve authorization/time ordering.

Known bottlenecks: per-item transactional flushes, branch/window service-policy reads, stock
hot-row serialization, finance organization-level journal lock, PostgreSQL auth-rate write
contention, token session read per request and index write amplification. Quote lookups are
batched, but representative multi-city/historical data and a distributed cache are still needed.
Redis safe-read caching is an adapter/invalidation design, not an implemented cache claim; never
cache authorization or stock correctness without explicit consistency rules. Introduce broker/
workflow adapters after reliability requirements are validated. Avoid sharding/Kubernetes now.
Partition raw GPS/audit only when retention and measured size justify the unique-key/FK tradeoffs.
