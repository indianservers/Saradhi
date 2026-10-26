# Monitoring and alerting

Implemented locally: opt-in Prometheus HTTP request counter/latency histogram with route templates (no query strings), database pool gauges and WebSocket active connection gauge. `/metrics` returns 404 by default. Enable only behind a private authenticated/network-restricted scraper. This is process-local instrumentation, not a monitoring service. No OpenTelemetry tracing, alert rules, centralized log pipeline, SLO dashboard or business-event metrics are configured.

Release alert set/owner to define: checkout error/latency, stuck pending orders, ledger mismatch, webhook failures, COD discrepancy age, dispatch backlog/time, GPS staleness, merchant acceptance delay, worker oldest-job/queue lag, DB pool saturation, Redis errors, API 5xx, AI provider failures and backup age. Use low-cardinality labels; never label user, phone, order, merchant, GPS or payment identifiers. Define severity, paging hours, escalation and runbook links with operations before launch.
