# OWASP ASVS 5.0.0 verification matrix (Phase 11)

This is a traceable, risk-focused mapping to ASVS 5.0.0 and OWASP API Security Top 10 (2023), not a claim that all ASVS requirements were verified. Results describe a source/test review on 2026-10-27.

| Control area / ASVS mapping | Surface | Test / evidence | Result | Remediation / retest |
|---|---|---|---|---|
| Authentication, credential storage, session lifecycle (V6/V7) | `/auth/*`, identity service | Argon2, token rotation/reuse code review; auth tests; production settings regression | Partial; SEC-01 fixed | Production key-path rejection and registration auth guard; 7 auth tests pass. OTP delivery, expiry abuse and production OIDC lifecycle not independently exercised |
| Access control / BOLA (V8; API1/API5) | owner resources, merchant/city/finance scopes, WebSocket | Integration authorization cases and DB-current `scoped()` review | Partial | Expand systematic role × object × property × WebSocket negative matrix; cross-city export tests remain open |
| Input validation / injection (V1/V2; API3) | FastAPI schemas and SQLAlchemy queries | Typed schema/query construction review; max page limit 100; no dynamic SQL interpolation found in searched backend | Partial | Dedicated injection payload tests / DAST not run |
| API resource limits (API4) | all HTTP endpoints | Auth endpoints have shared PostgreSQL buckets; DB/request timeouts and pagination bounds reviewed | Fail / gap | No global endpoint quotas or representative exhaustion test; SEC-02 open |
| Cryptography / transport / configuration (V11; API8) | settings, provider calls, deployment | Production TLS/OIDC/HTTPS validation code reviewed; integration auth uses ephemeral key | Partial | No deployed TLS/header/cookie verification; production configuration not started |
| Payment integrity / webhook authenticity | Razorpay APIs | Fake-provider integration covers invalid signature, dedupe, unmatched event, amount/capture flow; adapter uses constant-time HMAC | Partial | No live provider, out-of-order matrix or all refund transitions; credentials unavailable and intentionally not requested |
| Logging and privacy (V16) | HTTP middleware and shared logger | Logger fields inspected; logs request id/status/duration, not body or auth headers | Partial | No full PII scan, retention/access audit, or mobile location privacy exercise |
| Secure architecture / trust boundaries (V13/V15; API10) | AI, provider integrations, worker | Agent/provider boundaries inspected; deterministic defaults and unavailable providers noted | Not verified | Prompt injection, SSRF deployment policy and tool authorization abuse tests open |
| Mobile security (OWASP MASVS-aligned) | Customer / Merchant / Pilot Flutter | Source/config inventory only; Flutter SDK absent | Not tested | Secure storage, permissions, deep links, offline and device lifecycle test matrix open |
| Web client security | Admin / City Ops / Support Next.js | Typecheck and production builds; no browser E2E or session-expiry exercise | Partial | Playwright auth/RBAC/cookie/CSRF/XSS scenarios open |
| Secure deployment / dependency hygiene | CI, Docker, dependencies | CI and Docker reviewed; npm audit reported zero; pip-audit/SBOM tool unavailable | Partial | Python/package/container scan, secret history scan and CI enforcement open |

Retest state: SEC-01 tests pass. All `Partial`, `Fail`, and `Not tested` rows remain explicit blockers to a complete ASVS assessment.
