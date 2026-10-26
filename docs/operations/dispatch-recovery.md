# Dispatch recovery runbook

1. Check `/health/capabilities` and database/Redis health. If Redis is down, keep PostgreSQL business transitions authoritative; restore Redis before relying on live presence or cross-instance events.
2. Restart workers safely: outbox events use leased claims and can be retried; offer expiry uses bounded `SKIP LOCKED` claims. Inspect dead-letter/outbox state before replay.
3. On client reconnect, fetch order/delivery snapshot and timeline, then resume event consumption. Never infer assignment from a transient notification.
4. If a map provider times out or is unconfigured, ETA fails explicitly; do not substitute straight-line distance as road ETA.
5. Investigate quarantined GPS points without automated punitive action. Honor consent revocation and retention policy.
6. Manual reassignment requires scoped city operations authorization and a reason; verify stale offers are invalidated and review the dispatch audit record.

PostGIS, Redis and a road-routing provider are absent in the current local environment. Spatial eligibility, live multi-replica fan-out, and road ETA require those dependencies before production use.
