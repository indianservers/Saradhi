# Authorization test results

Real PostgreSQL-backed HTTP integration tests verify login token rotation/replay revocation,
logout, customer denial of administrative writes, merchant denial of another organization's
branch mutation and stock access, owner-bound order access, merchant/customer transition
boundaries, and wrong-pilot acceptance denial during an exclusive assignment race. The API
resolves current database sessions, role grants, memberships, permissions and resource scope;
token role text alone does not authorize a write.

The suite run after the outbox revision passed 21 tests; later targeted tests for address grouping,
recurrence and merchant payment denial each passed. The cross-organization test itself passed in
that full run. Negative-path responses avoid exposing DB errors and validation input; request IDs
are generated or sanitized. Authentication endpoint limits are durable/shared PostgreSQL
counters.

There are no PostgreSQL row-level security policies. Authorization is enforced in the API's
scoped service/repository path; callers with direct database credentials would bypass that layer.
Production runtime credentials therefore must remain private and least-privileged. General
endpoint rate limiting, trusted proxy/NAT-aware limits, managed secret injection, ingress WAF,
mobile credential storage and web cookie/CSRF integration remain deployment/client gates. This
is evidence for the covered tests, not a formal penetration test or exhaustive route proof.
