# Infrastructure boundaries

Local Compose preserves the developer PostgreSQL instance and offers Redis plus optional API/worker containers. AWS and DigitalOcean Terraform roots and API/worker Kubernetes manifests are reviewable deployment starting points; they are not provider-validated in this environment and have not been applied. They do not constitute an end-to-end production deployment. See `docs/deployment/` for architecture, prerequisites, limitations and runbooks. No cloud resources were created.
