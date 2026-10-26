# Real-time logistics

The FastAPI backend is the shared API for customer, merchant, pilot and operations clients. PostgreSQL is authoritative for tasks, assignments, consent, event history and ETA estimates. Redis is an ephemeral GEO/cache and Pub/Sub layer; the transactional outbox remains the recovery source for business events. Clients request a fresh REST snapshot after reconnect.

The `/api/v1/realtime` WebSocket requires a short-lived, single-use ticket and scoped channel (`order`, `pilot`, `merchant`, or `city`). Resource authorization occurs before subscribe and is periodically rechecked. Redis-backed connection quotas, heartbeats and bounded message sizes are implemented. Cross-instance live delivery is unavailable until Redis is running; this is surfaced by `/health/capabilities`.
