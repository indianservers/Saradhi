# System overview

Six role-specific clients share one versioned FastAPI API. Three Flutter applications consume
shared core, design and networking packages. Three Next.js applications consume shared UI and
the generated typed SDK. Clients never connect directly to PostgreSQL, Redis or AI providers.

The API is one stateless deployable modular monolith, with a separate worker process.
PostgreSQL is authoritative. Redis supplies cache/ephemeral presence/rate-limit coordination
and a demo job queue, never financial truth. Object storage sits behind ObjectStorage.

Flow: client -> TLS ingress -> authentication -> authorization/ownership -> transport adapter
-> application service -> domain rules -> repository/unit of work -> PostgreSQL.
Application services explicitly coordinate cross-context calls; repositories are private.
External effects will be recorded in a transactional outbox before asynchronous delivery.
There is no implemented business event relay or workflow engine in Phase 1.

The liveness endpoint only checks process responsiveness. Readiness requires PostgreSQL SELECT 1
and Redis PING, with bounded timeouts and no credential disclosure. API startup does not run
migrations, create tables, or require a reachable database. /api/v1/me verifies real JWTs when
configured and fails closed otherwise. No admin mutation endpoints are exposed.

AI gateway will receive a scoped principal and policy-approved tools, with human approval for
material actions. Agents never receive unrestricted database or shell access.
