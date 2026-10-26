# Phase 11 platform inventory

Audit date: 2026-10-27. Scope is the checked-out repository and its local test configuration. No cloud accounts, production systems, or third-party services were accessed.

## Applications and entry points

| App | Stack / current routes | Automated coverage observed |
|---|---|---|
| Customer | Flutter; one `lib/main.dart` entry point and a widget test | Widget test exists; Flutter SDK unavailable, so analysis/tests/build not run |
| Merchant | Flutter; one `lib/main.dart` entry point and a widget test | Same limitation |
| Pilot | Flutter; one `lib/main.dart` entry point and a widget test | Same limitation; background location/mobile permission behavior unverified |
| Company Admin | Next.js `/`, `/login`, `/workspace`, session and backend proxy routes | Typecheck and production build run; no Playwright suite found |
| City Operations | Next.js `/`, `/login`, `/workspace`, session and backend proxy routes | Typecheck and production build run; no Playwright suite found |
| Support Console | Next.js `/`, `/login`, `/workspace`, session and backend proxy routes | Typecheck and production build run; no Playwright suite found |

## Backend / platform map

- FastAPI v1 router: 153 registered routes at inventory time; `backend/api/v1/routes.py` is the dominant endpoint module. Additional health/readiness routes and `/api/v1/realtime` WebSocket are in `backend/api/app/main.py`.
- ORM metadata: 259 registered tables across 13 schemas; 198 foundation model registrations. These are model definitions, not a claim that every table was individually inspected against production data. Alembic contains 19 version files.
- Schemas include identity, merchant, geo, catalog, inventory, commerce, fulfillment, finance, operations, integration, audit, engagement, and intelligence.
- Background work: ARQ Redis worker relays outbox events, expires dispatch offers, runs bounded maintenance, and materializes recurring-order review occurrences. Queue name is `quickbuddy:demo`; worker source explicitly identifies it as a demo worker, not a complete production order/payment engine.
- Domain/event boundaries: transactional outbox, inbox dedupe, audit events, order history, dispatch events, and payment webhook inbox are present. In-process application services cover commerce, identity, dispatch/logistics, finance, recurring plans, payments, city launch, maintenance, and AI agents.
- AI: deterministic/optional provider gateway, agent tool registry, and prediction/optimization modules. No trained production model or external inference service was exercised.
- Payment/provider: Razorpay adapter is disabled by default and makes HTTPS API calls only when enabled; isolated fake-provider tests exist. Sandbox finance is test-only. Maps routing is an explicit unavailable provider by default. OTP provider is a protocol and is not configured in this local environment. Redis/PostgreSQL are infrastructure dependencies.
- Secrets/configuration: `.env` is ignored; `.env.example` carries placeholders. Settings require production DB TLS and OIDC, HTTPS origins, and separate controls for live Razorpay. Local key files are ignored. No secret values are reproduced in this inventory.
- Infrastructure: PostgreSQL/asyncpg, optional PostGIS, Redis, ARQ, Docker Compose, GitHub Actions. Compose has Redis by default and API/worker only under the `full` profile; the local test suite uses a guarded loopback `quickbuddy_test` database.
- CI currently runs Ruff, pytest, source/structure checks, OpenAPI drift, TypeScript checks, formatting and Next.js builds, plus a Redis worker smoke job. No Flutter, browser E2E, load, backup restore, or automated vulnerability scanner job was found.

## Existing controls and gaps

Present controls include current-database role/scope checks, owner checks, bounded page sizes (max 100), typed request schemas, Argon2 password hashing, refresh-token rotation/reuse revocation, durable auth attempt buckets, rate-limited/expiring OTP challenges, consumed single-use WebSocket tickets, short request timeouts, DB statement/lock/idle-transaction timeouts, TLS production guards, signed payment verification, webhook inbox dedupe, financial approval workflows, database immutability triggers, and isolated integration fixtures.

No code was removed. The repository does not contain a full city-wide route/screen catalog, mobile secure-storage evidence, a Playwright E2E suite, trained AI model assets, configured live maps/OTP/payment providers, production topology, or tested cloud backup/restore. No abandoned code was deleted because dependencies were not proven absent.
