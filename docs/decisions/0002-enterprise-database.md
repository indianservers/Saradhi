# ADR 0002 — Enterprise database and local validation

Status: implemented, with explicit external integration limits.

Reuse PostgreSQL 17.11 binaries for an explicitly user-approved isolated cluster on 5433.
Store data only inside .local/postgres-data; do not modify the unrelated 5432 server. Use
separate dev/test databases and owner credentials, never drop/reset existing databases.
Application owners are non-superusers; production must further separate migration/runtime roles.

Use thirteen PostgreSQL namespaces, typed core ORM and mapped relational foundations, UUIDv4
on Python 3.12, numeric/Decimal money, timestamptz and IANA local schedules. Keep one Alembic
history with frozen DDL artifacts, database financial/scope guards and additive hardening.
Prefer complete guarded vertical operations over generic CRUD for hundreds of tables.

Password/session authentication and refresh rotation now work against PostgreSQL. Authorization
uses current membership/permission/resource scope rather than token claims alone. OIDC remains
an adapter with external subject provisioning still pending. No default privileged user exists.

Use transactional outbox/inbox, at-least-once provider interfaces, and PostgreSQL-backed local
maintenance/notification handoff. Redis remains optional prepared infrastructure for caching/jobs;
no Redis-only financial state or in-memory recurring-order authority. Actual delivery polygons
require PostGIS and a reviewed spatial migration; block courier serviceability until available.

Keep payment tests deterministic and explicitly sandbox-only; no provider network effects,
production charges, live payouts, frontend screens or cloud provisioning in this phase.
