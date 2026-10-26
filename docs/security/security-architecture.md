# Security foundation

No public admin endpoints, default accounts, secret signing keys or auth bypasses exist.
OIDC verifier accepts RS256 only, with signature, issuer, audience, expiry, issued-at and
subject checks. JWKS URL is trusted configuration, never token input. Misconfiguration fails
closed. Production settings require HTTPS OIDC/origins and verified database TLS.
Future password authentication uses Argon2id PasswordHasher, per-user salts and rehash checks.

Access tokens are short lived; refresh tokens require separate rotation, reuse detection,
revocation and secure session storage. This lifecycle and OIDC callback are not implemented.
Next.js guards validate HttpOnly qb_access cookie through /api/v1/me and enforce role on the
server. Future callback must set Secure/SameSite cookies; mutating browser routes need CSRF
and Origin protections. Public root is a data-free shell, /workspace is protected.
Mobile tokens use Keystore/Keychain through flutter_secure_storage, never plain preferences.
Review platform backup exclusions, device migration and logout/revocation before release.

Central RBAC is only coarse access control. Every resource repository boundary must apply
owner/tenant/city/branch scope; future ABAC checks act on verified claims and DB membership.
AI inherits the user's exact scope, with a second authorization check inside every tool.
No AI unrestricted DB/admin execution. Audit financial/permission/AI actions to a restricted,
append-only sink with actor, action, resource, request ID and decision; AuditSink is an interface.

Logs deliberately exclude tokens, request bodies, query strings, PII and exception strings.
JSON logs carry request IDs, status and timing. Error envelopes hide validation input and
tracebacks. Bounded correlation IDs reject arbitrary log content. No wildcard CORS;
localhost dev origins are explicit. Production traffic requires TLS ingress, secure headers,
secret injection, dependency/image scans and observability without PII.

Authentication rate-limiting design: shared Redis atomic counters by trusted client IP plus
normalized identity fingerprint; bounded windows, burst caps, Retry-After and audit on abuse.
Ingress handles volumetric limits and trusted proxy validation. No login/password mutation
endpoint exists yet; enable/test distributed limits before adding one. Do not claim rate limits
are already enforced. Redis outage policy must fail closed on sensitive authentication actions.
Secrets stay in ignored .env or external secret manager; never bake into images or client bundles.
