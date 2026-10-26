# Cloud portability

No cloud resources have been provisioned. Runtime uses environment variables, no Windows
paths. API/worker images run non-root and keep no authoritative state on local disk. Object
uploads must use ObjectStorage adapters with signed URLs, limits, content validation and
malware scanning. Local upload adapters, if introduced, are development-only.

AWS path: TLS ALB -> ECS/Fargate API and worker services -> private managed PostgreSQL
(RDS with optional PostGIS), managed Redis, S3 and Secrets Manager. Logs/metrics/traces through
OpenTelemetry to provider adapters. Broker/workflow candidate: SQS/EventBridge and Temporal
or reviewed alternatives; evaluate ordering, replay, DLQ and workflow guarantees first.

DigitalOcean path: App Platform or containers on droplets -> managed PostgreSQL/Redis-compatible
service -> Spaces object storage and injected secrets. Validate extension support, backups,
connection limits and region before selection. Put private traffic and ingress TLS controls
in place. These are architecture notes, not deployable infrastructure claims.

Scale API and workers independently; bound DB pool budgets. Migrations run once per release
as a controlled job, never per API replica. Rolling rollout gates on readiness and contract
compatibility. All replicas share PostgreSQL and durable event infrastructure; process memory
is never a session/lock authority. Kubernetes and Terraform directories are reserved only;
no cluster complexity is required in Phase 1. Select provider after budget/region/SLO review.
