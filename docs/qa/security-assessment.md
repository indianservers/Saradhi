# Phase 11 security assessment

Assessment date: 2026-10-27. This is a bounded repository and local-test assessment, not a penetration test or vulnerability-free attestation. Baseline references: [OWASP ASVS 5.0.0](https://asvs.owasp.org/) and [OWASP API Security Top 10 (2023)](https://owasp.org/www-project-api-security/).

## Findings

| ID | Severity | Finding / impact | Remediation and retest |
|---|---|---|---|
| SEC-01 | High (configuration-dependent) | A production configuration containing `AUTH_PRIVATE_KEY_PATH` selected `LocalTokenVerifier` before OIDC, and `/auth/register` did not require the local auth mode. This could unintentionally expose local password-token authentication/account creation in an OIDC deployment. | Fixed: production settings reject local signing key paths; local registration now calls the same local-auth mode guard as login. Regression tests pass (see `test_auth.py`). |
| SEC-02 | Medium | API-wide request throttling is not present; durable shared throttling is scoped to registration/login/refresh/OTP. Expensive authenticated endpoints therefore rely on infrastructure-level controls not evidenced here. | Open. Add per-route / principal / network quotas and deployment gateway limits with abuse-safe metrics. |
| SEC-03 | Medium | No automated dependency/secret scanner or SBOM generator was available in the local environment; manual checks cannot establish clean supply chain or secret history. | Open. CI gates and historical repository scanning are required. |
| SEC-04 | High readiness gap | Cross-app mobile/browser security, complete object-property authorization matrix, AI prompt/tool abuse suite, and production-like fault injection were not run. | Open; see the per-domain evidence documents. |

## Verification performed

- Read settings, FastAPI middleware, auth and authorization helpers, route inventory, webhook adapter/application flow, ORM/invariant setup, Docker/CI configuration and existing integration tests.
- Ran backend unit, integration and contract suite against guarded local PostgreSQL: 95 passed, 1 deprecation warning. Ran the updated auth-focused suite: 7 passed.
- Ran npm dependency audit: zero reported vulnerabilities (including production-only audit). The result applies to the lockfile and npm registry advisory data available at run time.
- Production configuration regression tests cover OIDC-only acceptance, local-key rejection, and the local-registration guard under OIDC. The production ASGI deployment was not started.
- No destructive tests, production traffic, third-party credentials, actual Razorpay calls, or real user data were used.

## Readiness

One configuration-dependent high-severity auth defect was found and fixed. The open scope gaps mean this evidence does not meet the requested release gates. See `phase-11-final-report.md`.
