# Infrastructure boundaries
Dockerfile and local Compose are executable foundations. AWS, DigitalOcean, Kubernetes and
Terraform directories reserve future deployment work; no cloud provisioning or cluster is
implemented. See docs/deployment/cloud-portability.md. Observability currently consists of
JSON request logs and bounded health checks; OpenTelemetry/metrics/alert adapters are planned.
CI definitions live in .github/workflows; ci_cd is reserved for future deployment tooling.
