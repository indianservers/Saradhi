# DigitalOcean deployment (review only)

`infrastructure/terraform/digitalocean` describes a VPC, managed PostgreSQL/Redis, private Spaces bucket, container registry and autoscaling DOKS cluster. It is a starting template, not provider-validated or applied. Terraform CLI/provider schema validation was unavailable in this environment.

Prerequisites: account/region approval, budget and spending alerts, private encrypted remote Terraform state, identity/token handling through CI federation or short-lived credentials, Spaces access policy, private cluster connectivity, secrets, and a reviewed plan. Avoid committing `.tfvars`, API tokens or state. Run `terraform init -backend=false` and `terraform validate` in both the root and CI; inspect plan and cost before any separately authorized apply.

The manifests only cover API and worker. No ingress/TLS, web apps, DNS, managed secret integration, full monitoring, or restore evidence is present. Verify managed PostgreSQL PostGIS/version/backup support and Redis TLS/auth, private networking and connection budgets in the chosen region before migration. No provisioning occurred.
