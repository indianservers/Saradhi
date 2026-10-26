# Web production release

Apps: company admin, city operations, support console. All three Next.js workspaces have standalone output enabled, monorepo tracing root configured, and production builds passed. Docker image build could not be verified because Docker is unavailable.

Build each workspace using `npm run build --workspace=@quickbuddy/company-admin` (and `@quickbuddy/city-operations`, `@quickbuddy/support-console`). Set server-only API and WebSocket endpoints at runtime; never use `NEXT_PUBLIC_` for secrets. Configure HTTPS, secure cookie/session policy, exact CORS, CSP/security headers, server-side role checks, health endpoint, error logging, static cache policy and access controls. Validate deep links, expired-session recovery, authz per role and browser E2E before release. The AWS/Kubernetes templates do not deploy these web services. No DNS change was made.
