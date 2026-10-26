# Cloud cost model (parameterized; no provider prices asserted)

Use the providers' current regional calculators at decision time. This file intentionally supplies no current prices. Monthly estimate formula: `Σ(quantity_i × hours_i × rate_i) + usage charges + taxes/support`. Enter region, sizes, hours, data transfer, storage/IOPS, backup retention and log ingestion.

Scenarios (fill measured input cells):

| Scenario | API/worker hours | DB/cache | Storage/egress | Third parties |
|---|---|---|---|---|
| Development | `instances × hours` | smallest approved non-prod | test fixtures | low test usage |
| Controlled city pilot | measured replicas × hours | HA only if launch gate approves | observed media and GPS | measured SMS/maps/payment |
| 10k orders/day planning | benchmark-derived replicas | load-tested DB/cache and headroom | measured retention/CDN/egress | order, map, OTP and gateway volumes |
| Higher growth | scenario model, not linear extrapolation | benchmark/HA design | retention and egress model | contract rate quotes |

Include compute, PostgreSQL, Redis, object storage, CDN, load balancer, NAT/egress, logs/metrics/traces, backup, AI inference, map/SMS, Razorpay fees and support. Set per-environment budgets and alert thresholds before provisioning. Obtain provider quotes; scale from workload tests, not theoretical capacity.
