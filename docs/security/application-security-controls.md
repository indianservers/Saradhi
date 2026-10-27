# Application security controls and deployment requirements

## Implemented in the application

- Private FastAPI operations use bearer-authenticated actors; sensitive data paths use live database role assignments, organization membership, branch/city scope, or resource ownership. Unknown/unestablished authority is denied.
- Login, registration, refresh, and OTP verification use durable PostgreSQL identity and network rate buckets. OTP creation is now rate-limited as well. API-wide network budgets and stricter AI/search/export families are shared by instances through the database. Selected expensive operations also use actor plus network budgets.
- Forwarded client addresses are ignored by default. Configure `TRUSTED_PROXY_CIDRS` only for actual proxy networks; the resolver walks the forwarding chain from the trusted peer and ignores client-provided headers otherwise.
- Request bodies are bounded by `MAX_REQUEST_BODY_BYTES` (default 6 MiB); branch CSV import retains its stricter 5 MiB, 5,000-row, 20-column, and 2,000-character-cell limits. Pydantic write models reject unknown fields. Pagination and batch schemas have explicit upper bounds.
- Kitchen task/station APIs now require `kitchen.manage`; kitchen operators no longer inherit broad merchant administration or inventory-read permission. Merchant member assignments remain limited to `branch_manager` and `kitchen_operator`, require a scoped organization-members grant, target an active account, and emit an audit event.
- Public customer discovery only exposes approved, active, accepting branches and current prices/open windows. Existing protected exports are scope-filtered, bounded, no-store, and audited.
- 401, 403, and 429 outcomes have low-cardinality Prometheus counters; request logs contain route, status, request ID, and duration only, never request bodies or bearer tokens.

## Deployment configuration still required

- Kubernetes allows API ingress only from the `ingress-nginx` namespace, but this repository contains no `Ingress` resource, WAF, public hostname, or TLS certificate binding. Attach the service to the approved TLS ingress and configure ingress-level rate/concurrency limits, connection/timeouts, and a body-size limit there. Use a managed WAF/DDoS service for distributed attacks. Application limits are not a substitute for edge DDoS controls.
- If ingress-nginx forwards `X-Forwarded-For`, set `TRUSTED_PROXY_CIDRS` to the exact ingress/controller egress CIDRs in the production secret/configuration. Do not trust `0.0.0.0/0` or public client ranges. Until configured, the API uses the proxy peer address, which can group legitimate users behind one proxy.
- Keep PostgreSQL reachable only from approved API/worker networks and preserve TLS/credential configuration. Rate limiting fails closed with 503 when its PostgreSQL store cannot be reached.
- Configure alerting for `quickbuddy_security_events_total{event="authorization_denied"}`, `...{event="authentication_denied"}`, `...{event="request_throttled"}`, 5xx rates, and readiness failures. Scrape `/metrics` only from the private monitoring network.
- NetworkPolicy restricts inbound pod traffic but does not independently mitigate volumetric or distributed denial of service. Validate ingress/WAF policy in the target cluster before production exposure.

## Verification

Security regressions are in `backend/tests/test_security_controls.py` and `tests/integration/test_security_hardening.py`. The integration fixture only uses local `quickbuddy_test`; never run destructive database commands against development or production.
