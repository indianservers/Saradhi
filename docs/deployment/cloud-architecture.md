# Cloud architecture and boundaries

Quickbuddy remains a stateless FastAPI API plus independently scaled ARQ worker, three Next.js standalone web apps, PostgreSQL/PostGIS as the transaction authority, and Redis for transient queue/fan-out. Put API and web entry points behind HTTPS load balancing; keep PostgreSQL and Redis on private networks. Store secrets in managed secret services and inject at runtime.

The AWS template includes VPC, private data subnets, RDS, ElastiCache, S3, ECR, ECS API/worker and ALB. It does not yet deploy the Next.js apps, configure DNS, provision certificates, or create a complete telemetry stack. DigitalOcean template provides VPC, managed database/cache, Spaces, registry and DOKS. Kubernetes manifests cover API/worker only; no ingress/TLS or web deployment. These are reviewable starting points, not production blueprints.

Keep staging and production databases, Redis, buckets, OIDC audiences, payment/webhook secrets and integrations distinct. DB is authoritative; do not use Redis as order/payment state. No sticky sessions should be needed for correctness when WebSocket events are fanned out through shared Redis and reconnects fetch an authoritative snapshot.

Start with bounded pools and calculate `replicas × (pool_size + max_overflow)` per process role plus migrations/admin. Defaults allow 15 connections per engine; set `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=1` as an initial cap, then size from provider connection limits. PgBouncer transaction-pool compatibility is unverified: asyncpg prepared/session behavior and connect-time session settings require explicit validation. Never send writes to read replicas.

Target scale requires measured workload and bottleneck data. The repository has no evidence for 10,000 orders/day capacity.
