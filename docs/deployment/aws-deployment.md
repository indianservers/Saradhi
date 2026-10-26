# AWS deployment (review only; do not apply from this guide)

The root at `infrastructure/terraform/aws` describes VPC/subnets/NAT, RDS PostgreSQL, Redis-compatible ElastiCache, private S3, ECR repositories, ECS API/worker, CloudWatch logs and an HTTPS ALB. Terraform state backend and KMS policy are not configured in code. Configure a private, encrypted, versioned remote state backend before any plan containing secrets; local state can retain Redis credentials.

Prerequisites: approved AWS account/region, cost budget, domain/certificate ARN, IAM federation, private state bucket/lock, secret ARNs, and explicit change approval. The root uses variables/placeholders; do not put credentials in `.tfvars`. Review `terraform init -backend=false`, `terraform validate`, then a credentialed `terraform plan` only after approvals. Never run `apply` without a reviewed plan and separate authorization. No plan was run here.

Before use, validate provider schemas and network rules. The template does not deploy Next.js apps, create DNS records/certificate, install application secrets, or configure full alerting. Run staging migration, smoke, load and restore drills first. Runtime DB credential must be a least-privilege app role, not the managed DB owner. Estimate costs from current provider calculator and actual sizing; this guide quotes no prices.
