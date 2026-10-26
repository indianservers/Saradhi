# Phase 2.A API audit

The generated OpenAPI remains the API source of truth. Routes use typed Pydantic request and
response schemas, bounded page sizes (1..100), opaque cursors and allowlisted ordering. Domain
errors use a common structured envelope with request IDs; unhandled/database details are
suppressed. The current envelope is project-specific rather than a complete RFC 9457
Problem Details implementation. Success responses commit before the client receives success.

Authentication and resource tests cover invalid and expired/replayed tokens, refresh rotation,
logout, customer/merchant role boundaries, cross-organization branch/hour and stock denial,
resource ownership and rejected fake admin writes. Database membership/permission/resource
scope is consulted at write time; frontend role claims are not sufficient. Auth routes have
durable PostgreSQL rate buckets, but general API throttling depends on trusted ingress and is
not configured globally. No general API request-rate benchmark was run.

The cart/quote/confirm flow persists quote inputs, groups merchant orders and fulfillment units,
reserves stock/slots atomically, and supports idempotent confirmation. Repeated requests with the
same key replay the same order. Multi-merchant child rejection correctly blocks a parent sandbox
payment until revised allocation behavior exists. Courier serviceability fails closed because
PostGIS is unavailable on the local server. Payment, refund and webhook routes are explicitly
sandbox-only; there is no production provider adapter.

No API changes were made to replace the common response contract in this phase. API-level
authorization evidence is in `../security/authorization-test-results.md`; generated endpoint
inventory is in `api-reference.md` (if present) and OpenAPI artifacts.
