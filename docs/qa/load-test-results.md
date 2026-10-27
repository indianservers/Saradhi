# Load and performance test results

## 2026-10-27 bounded local mixed workload

The [app audit](app-audit-2026-10-27.md) adds a synthetic local ASGI/PostgreSQL
workload with cart creation/add/read/delete, merchant queue, catalogue, customer
tracking and company dispatch. Three short profiles use 1, 10 and 30 concurrent
journeys, totaling 1,728 requests with no unexpected response failures. At 30
concurrent journeys, measured p50/p95/p99 were 241.22/400.93/1695.27 ms and throughput
was 100.9 requests/second for that short profile. Full [raw measurements](app-stress-2026-10-27.json)
include per-route latency. These results exclude network latency, real payments,
carrier calling, WebSocket fan-out and production topology. They do not establish
production capacity or replace a long soak. API protection remains enabled;
profiles use separate synthetic test network identities to avoid cross-test bucket contamination.

## Earlier baseline


No representative Locust/k6 workload was available or executed. Destructive stress and long soak were not run. The full integration suite includes a bounded 100-concurrent checkout correctness test against local `quickbuddy_test`; the test asserts final order/stock/window invariants. It does not represent browsing, merchant, dispatch, GPS, websocket, notifications, payments, or dashboard traffic.

Measured hardware: 12 logical CPUs, 31.8 GiB RAM, Windows 11. Backend test suite: 95 passed in 106.30 seconds (includes DB migration/setup and all tests). Next.js builds are build-time checks, not request throughput tests. No API RPS/orders-per-second, p50/p95/p99, error-rate-under-load, DB CPU/connection saturation, Redis memory, worker lag or WebSocket capacity is claimed. Planned model and profile parameters are in `performance-workload.md`.

Load-test blocker: run profiles against isolated, representative PostgreSQL/PostGIS/Redis/API/worker infrastructure and capture resource telemetry before claiming planned capacity.
