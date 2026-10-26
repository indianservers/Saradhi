# API authorization and credential safety

Password registration creates only a customer identity. The same user can acquire merchant,
staff or pilot profiles; there are no duplicate per-app global users. Argon2id hashes passwords;
email uniqueness uses normalized lowercase storage. Password hashes never leave repositories.
Local RSA signing keys are generated explicitly into ignored .secrets; no embedded signing key,
default password or automatic super-admin registration. The local CLI grants a platform role
only to an explicitly named existing user and records an audit event.

Access JWTs use RS256, issuer/audience/subject/session/iat/exp validation and short 15-minute
lifetimes. Every local token verifies a live database session and active user. Refresh tokens
are high-entropy opaque values stored only as SHA-256 digests. Rotation consumes the old token;
reuse revokes the session family, and logout revokes outstanding access. Serialize refreshes in
clients to avoid a legitimate concurrent retry looking like reuse. OIDC verifier remains
available; external identity mapping/provisioning must be wired before enabling external users.

Authority comes from current database permissions, assignments, active organization membership
and city/branch scope, never solely from token roles or frontend checks. Platform global grants
are explicit; merchant self-onboarding grants merchant-owner scope only. Staff API can grant
only branch-manager/kitchen roles within the caller's authorized branch. Finance and global
admin grants are not public self-service. Resource owners are checked on addresses, carts,
orders, sessions, pilot actions and support tickets. Support does not inherit financial writes.

Authentication endpoints use durable shared PostgreSQL minute buckets for identity/token digest
and network digest. Limits default to 20 per minute; tests explicitly configure a higher limit.
No untrusted forwarded-IP header is used. Add trusted ingress limits and parameterized NAT-aware
policies for production. Rate limits commit even when credentials fail. OTP provider/pepper must
be configured; otherwise requests return 503, never a pretend SMS. OTP hashes use HMAC with
pepper, expire after five minutes, allow five attempts and are one-time; resend is throttled.

JWTs are delivered by API to authorized clients. Mobile must use Keychain/Keystore; web requires
an HttpOnly/Secure/SameSite server-side OIDC/password session callback. No callback/UI was added
in Phase 2, no token is stored in localStorage and no app screen was changed. Mutating web-cookie
routes need CSRF/Origin protection when introduced. Backend accepts bearer headers, not cookies.
CORS remains explicit, credentials are not allowed cross-origin, logs omit bodies/query strings,
secrets/PII and SQL error detail. KYC/proof/bank records store private object or token references.

AI tables persist scoped tool decisions/approvals only. No AI model gets unrestricted SQL,
database credentials or administrative shell. Any future money/dispatch/status tool must call
the same deterministic authorized services and separately enforce resource ownership and approval.
