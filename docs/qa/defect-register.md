# Phase 11 defect register

| Issue | Module | Severity | Reproduction / expected / actual | Root cause and fix | Regression / retest | Status |
|---|---|---|---|---|---|---|
| SEC-01 | Settings / auth registration | High, configuration-dependent | Set production OIDC settings and `AUTH_PRIVATE_KEY_PATH`; expected OIDC-only auth, actual startup selected local token verifier; registration route also lacked mode guard | Production mode allowed a local signer path and registration didn't call `local_auth()`. Production validator now rejects it; registration now requires local-auth mode. | `backend/tests/test_auth.py`: OIDC production config accepted, local key rejected, registration guard verified; 7 tests pass. | Fixed |
| SEC-02 | API edge | Medium | Authenticated high-cost routes have no shared API quota; expected bounded platform-wide consumption; actual only auth endpoints are throttled | General edge/per-principal limiter not implemented/configured | No test/telemetry | Open |
| QA-01 | Cross-app verification | High release blocker | Required mobile and browser workflows cannot be reproduced in current environment | Flutter SDK and Playwright suite absent | Next.js builds/typechecks only; Flutter not run | Open |
| QA-02 | Performance / resilience evidence | High release blocker | No representative load/soak, fault injection, or telemetry capture | Dedicated load/recovery environment absent | 100 concurrent checkout correctness only | Open |
| QA-03 | Backup recovery | High release blocker | No tested backup restored to disposable DB | Backup/restore runbook/tooling not evidenced | None | Open |
| QA-04 | Supply-chain assurance | Medium | Python/container/secret-history scans and SBOM not run | Scanner tools/gates absent | npm audit only, zero findings | Open |

No additional issue is silently accepted; open items block production readiness as recorded in the final report.
