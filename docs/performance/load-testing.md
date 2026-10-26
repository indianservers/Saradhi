# Load and performance evidence

The concurrency test generated 100 simultaneous authenticated checkout confirmations against
one local PostgreSQL branch and shared stock row. All 100 returned HTTP 201 in 2.914 seconds
(34.313 confirmation requests/second), using the ASGI in-process transport, PostgreSQL 17.11,
pool size 5 and max overflow 10. The result is reproducible from
`tests/integration/test_reliability.py::test_one_hundred_concurrent_checkout_transactions` and
stored in `../operations/concurrency-evidence.json`.

This demonstrates correctness under one bounded burst, not public-network throughput, sustained
capacity, p95/p99 latency, cloud performance, payment-provider speed, courier/GPS throughput or
production hardware sizing. It does not include load generators outside the process, realistic
data growth, multi-replica contention or soak/failover behavior. Query-plan samples in
`../operations/phase-2-database-evidence.json` use small fixtures. Plan capacity tests with
representative data volume, deployed ingress, worker count and DB connection budget before
choosing an SLO or replica count.
