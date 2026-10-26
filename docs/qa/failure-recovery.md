# Failure recovery assessment

Code has bounded database statement/lock timeouts, connection pre-ping, request/provider timeouts, explicit unavailable maps provider, disabled-by-default payments/AI, transactional outbox/inbox patterns, idempotent recurring occurrence materialization, Redis readiness checks and worker startup health checks. These are mechanisms, not evidence of tested HA.

| Failure | Test status |
|---|---|
| Redis unavailable / reconnect / event replay | Not injected; health/readiness and WebSocket fail-closed behavior inspected |
| PostgreSQL disconnect / recovery | Not injected; process/API DB errors map to retryable 503/409 responses |
| Worker termination/restart | Worker smoke exists in CI but was not run in this assessment; durable outbox/inbox reviewed |
| WebSocket disconnect/reconnect | Not browser/mobile tested |
| Maps unavailable | Explicit unavailable implementation is default; no external provider |
| AI unavailable | Gateway timeout/error code exists; external outage not injected |
| Razorpay disabled | Configuration test confirms payment unavailable with no key; no provider request |
| Merchant/pilot/customer process restart | Not lifecycle-tested on mobile |
| Notification outage / checkout disconnect | Not injected; checkout idempotency and outbox covered in integration suite |

No multi-node failover, RTO, or HA claim. Recovery drills and process-restart idempotency remain release blockers.
