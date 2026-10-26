# Capacity assumptions and benchmarking plan

10,000 placed/completed orders/day divided by 86,400 = 0.11574 order/s average.
This is a planning objective, not measured capacity. Test order creation at 10x = 1.1574/s,
configurable peak multiplier 50x = 5.787/s, and 100x = 11.574/s bursts. Distinguish placed,
completed, cancelled and in-flight orders in every benchmark report.

Initial traffic model: 30 API calls/order before browsing traffic; 10x order peak implies
34.7 requests/s from that flow alone. Model 2,000 browsing users at one request/10 seconds
(200 rps), and 1,000 active pilots emitting every 5 seconds (200 location events/s).
Parameterize all figures; do not infer GPS or API volume solely from orders. Multi-merchant
fanout, scheduled release bursts, retries and provider callbacks add independent traffic.

Benchmark Phase 2 against a representative indexed schema on named CPU/RAM/storage with
real PostgreSQL/Redis. Stages: warm-up 5 min; average 15 min; 10x 30 min; 50x 15 min;
100x 2 min bursts; 4-hour soak. Mix read/write/pilot events with merchant fanout and separate
browsing load. Test queue backlog recovery, slow providers, duplicate callbacks, dependency
outages, replica restarts and Redis loss. Verify no lost/double money postings or assignments.

Provisional acceptance targets for review: non-provider API p95 <300ms, p99 <1s, errors <1%;
order commit p95 <750ms; bounded queue lag <5s under steady peaks. Correctness gates trump
latency. Record lock waits, pool saturation, DB CPU/IO, cache hit rate and event delivery age.
No throughput validation is possible before order schema and flows exist.

The k6 health.js harness only measures liveness. Run `k6 run -e RPS=20 -e DURATION=60s
tools/load_testing/health.js` after installing k6 explicitly. It is not an order benchmark.

Use API replicas with no process-local auth sessions or correctness locks. Pool budget is
replicas * (pool_size + max_overflow) plus workers/migrations, reserved admin connections.
Default 5+10 is per process, not permission to increase replicas without DB sizing. Add
PgBouncer after testing asyncpg/prepared statements. Scale workers independently, introduce
broker/workflow engine when measured backlog and reliability needs justify it. Optimize
queries/indexes before sharding; partition tracking/audit only after retention/query analysis.
