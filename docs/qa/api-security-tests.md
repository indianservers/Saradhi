# API security tests and results

Scope: 153 registered v1 router endpoints were inventoried from the FastAPI router. Source review covered middleware, schemas, pagination, auth dependencies, owner/scope checks, payment routes and the realtime endpoint. This is not a route-by-route dynamic penetration test.

| Test | Evidence / outcome |
|---|---|
| Authentication bypass | Auth-focused unit tests: 6 passed. OIDC invalid-token cases and local/production mode guard covered. Full unauthenticated sweep across all 153 routes not run. |
| Object authorization | Existing API integration tests cover customer-owned order access, scoped finance/admin actions, pilot assignments, support, city controls and WebSocket-related authorization code. Not every route/role/property combination tested. |
| SQL injection / flexible filters | Backend uses SQLAlchemy expressions in inspected routes; no user-driven raw SQL or unsafe sort parameter found in targeted source search. No automated injection corpus/DAST run. |
| Pagination / resource use | Route `Limit` is constrained to 1..100; product recommendation limit is <=30. Auth flows use durable buckets. General API rate limits are missing (SEC-02). |
| Validation / mass assignment | Typed Pydantic input models reviewed in critical routes; no generic model update from arbitrary request dict was identified in reviewed auth/payment code. Full field-by-field test not run. |
| Webhook body | Razorpay webhook caps streamed body at 1 MiB, requires event id/signature headers and verifies raw-body signature in adapter. Fake-provider invalid-signature and duplicate-event integration tests pass. |
| Error handling | HTTP validation/internal/DB errors use structured responses; unhandled exception logs only request id. No provider response body or request body logging found in reviewed paths. |
| CORS / headers | Explicit origin allowlist; credentials disabled; `nosniff`, `no-store`, request id headers. Production requires HTTPS origins. Runtime browser policy not measured. |
| SSRF / file upload / path traversal / command injection | No general file upload or user-supplied command execution API identified in route inventory. AI provider URL is operator configuration, not request input; production requires HTTPS. Deployment egress allowlisting not verified. |

Commands: `.venv\Scripts\python.exe -m pytest backend/tests tests/unit tests/integration tests/contract -q` (95 passed); `.venv\Scripts\python.exe -m pytest backend/tests/test_auth.py -q` (6 passed); `npm audit --json` (0 findings reported). Findings and unexecuted scenarios are not treated as passes.
