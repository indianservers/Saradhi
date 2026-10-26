# Secrets inventory and rotation

| Secret | Consumers | Handling |
|---|---|---|
| OIDC client/service credentials, JWT/OTP keys | API and web auth | Managed secret store; short rotation overlap; never logs |
| PostgreSQL runtime/migration/report roles | API, release job, read-only reporting | Separate least-privilege roles; rotate and verify pool reconnect |
| Redis auth/TLS | API and worker | Managed secret store; restrict network and rotate |
| Razorpay keys/webhook secret | Payment service | Disabled until authorized; separate test/live; rotate webhook verification key with overlap |
| Firebase/notification/maps | Relevant services/apps | Per-environment restricted keys, mobile key restrictions |
| AI provider key | AI gateway | Server-side only, quota, HTTPS; provider disabled by default |
| Object storage access | Upload/download service | Workload identity; signed expiring private object access |

No provider integration for all these secrets is complete. Examples are placeholders. Use GitHub secret scanning and history-aware scanning before release; rotation is required if any credential appears in history. Do not print, paste or commit values. Rotate by adding new value, deploy consumers, verify, revoke old value and record owner/date.
