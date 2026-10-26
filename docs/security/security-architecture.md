# Security architecture — Phase 2

Current implemented authentication/authorization details are in ../api/api-security.md and
../api/error-contracts.md. Password login, rotation, replay revocation, logout, local RS256,
OTP provider contracts, committed rate limits and database resource scoping now exist.
The Phase 1 statement that password authentication was future work is superseded.

No default account or public super-admin registration exists. Local platform provisioning
requires an explicit named existing user through a local operator command with an audit event.
Merchant self-onboarding grants only its own organization scope. Current DB membership and
permission/resource scope are authoritative; token roles alone never authorize resource writes.
Support permissions cannot change bank references or perform finance operations. Refund requests
and decisions require different actors and matching approval records. Posted money is immutable.

Secrets/data live in ignored .env/.secrets/.local with restricted Windows ACLs. Production must
use managed secrets, separated DML/migration roles, verified DB TLS and trusted ingress limits.
Structured logs omit bodies, query strings, tokens, customer location/PII and raw exception SQL.
Mobile/web secure credential storage and CSRF/callback work remain client-integration gates.
No frontend auth bypass, AI unrestricted SQL, real gateway transaction or cloud deployment exists.
