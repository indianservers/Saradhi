# ADR 0001 — Phase 1 foundation

Status: accepted for scaffold; revisit with measurements and Phase 2 review.

Use modular monolith FastAPI plus independently deployed worker, shared PostgreSQL and Redis.
Six apps remain separate build targets; share presentation/network contracts, not role-specific
business logic. Riverpod/GoRouter for Flutter; Next.js App Router and npm workspaces for web.
FastAPI OpenAPI is contract authority; generate TypeScript types and document pinned Dart toolchain.

Fail closed for identities until OIDC is configured. Public shell contains no live business data.
Preserve existing PostgreSQL; no server installation or business migrations. Redis/ARQ demonstrate
jobs only and do not promise exactly-once delivery or durable financial workflows. Interfaces
reserve transactional outbox, idempotent consumers, audit and object storage. Prefer ports to
provider coupling; no Kubernetes or provider provisioning in Phase 1.

Tradeoffs: local Flutter validation is blocked by missing SDK, auth sign-in UX waits for an
identity provider, and DB/queue tests require authorized infrastructure. Do not substitute mocks
for these integration results. Domain context packages use documented internal conventions
instead of hundreds of empty repository/service files.
