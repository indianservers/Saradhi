# Performance workload model

Planning baseline from the brief: 10,000 orders/day. A flat average is 0.116 orders/second and is not a peak sizing target. For an initial model only, assume 35% of orders arrive in a 4-hour peak: 3,500 / 14,400 = 0.243 orders/second; use 3x peak burst = 0.729 orders/second. These are planning assumptions, not validated product traffic.

Representative journey should include home/config (1), merchant search (2), catalogue browse/details (3), cart writes (3), quote (1), confirmation (1), payment events (2), merchant queue/accept (2), dispatch/offer (2), pilot GPS (one update every 15 seconds while active), tracking snapshot/socket updates (1 subscription plus event fan-out), notification delivery, completion (2), and dashboard polling (operator concurrency dependent). The API calls/order estimates are intentionally provisional; GPS and dashboard load are modeled separately.

Profiles: A smoke 1 user / 1 minute; B normal local test workload 5 users; C planned target 0.243 order starts/s with explicit browse/GPS mix; D burst 3x and configurable; E stress increase only on isolated owned infra; F soak duration configurable and run only on dedicated environment. No Locust/k6 scenario was present or executed, so none of these profiles are capacity evidence.

Measured host: Windows 11, 12 logical CPUs, approximately 31.8 GiB RAM. Environment has a single local PostgreSQL test database and no verified production topology. No throughput, database CPU, p95/p99, queue lag, socket fan-out, or saturation number is claimed. The 100-request checkout integration test checks correctness, not a realistic 10k/day performance profile.
