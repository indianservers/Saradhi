# Environment configuration

Profiles: local `development`; CI `test`; cloud `staging`; customer-facing `production`. Example placeholders live in `infrastructure/environments/{staging,production}` and are not deployable unchanged. Use separate identities, databases, Redis, buckets, OIDC audiences, payment/webhook, notification, maps and AI secrets per environment. Never point staging at production finance/operations.

Staging/production settings enforce PostgreSQL async driver, TLS flag, HTTPS OIDC issuer/JWKS and HTTPS CORS origins, and forbid local password signing keys. Keep `METRICS_ENABLED=false` until scrape access is restricted. `RAZORPAY_ENABLED=false`, mode disabled, and live approval false are intentional. Confirm TLS certificate verification in the actual driver/provider configuration; `DATABASE_SSL=true` alone is not evidence of correct CA/hostname validation.

Runtime startup should receive only its environment. Do not place credentials in Next.js public variables, Docker build args, Terraform variables, CI logs or browser bundles. Validate settings with startup checks and redacted diagnostics.
