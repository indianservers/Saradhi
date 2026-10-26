# Load and performance test results

No representative Locust/k6 workload was available or executed. Destructive stress and long soak were not run. The full integration suite includes a bounded 100-concurrent checkout correctness test against local `quickbuddy_test`; the test asserts final order/stock/window invariants. It does not represent browsing, merchant, dispatch, GPS, websocket, notifications, payments, or dashboard traffic.

Measured hardware: 12 logical CPUs, 31.8 GiB RAM, Windows 11. Backend test suite: 95 passed in 106.30 seconds (includes DB migration/setup and all tests). Next.js builds are build-time checks, not request throughput tests. No API RPS/orders-per-second, p50/p95/p99, error-rate-under-load, DB CPU/connection saturation, Redis memory, worker lag or WebSocket capacity is claimed. Planned model and profile parameters are in `performance-workload.md`.

Load-test blocker: run profiles against isolated, representative PostgreSQL/PostGIS/Redis/API/worker infrastructure and capture resource telemetry before claiming planned capacity.
