# CI/CD and release gates

Current GitHub Actions validates backend format/lint/tests against disposable PostgreSQL, worker smoke against Redis, Python dependency audit, web workspace typecheck/format/build and npm audit. Phase 12 adds Terraform validation without credentials/apply when Terraform is available. Pipelines do not deploy production, build/sign all images, produce SBOMs, scan containers, run Flutter builds, perform browser E2E or sign artifacts.

Target flow: commit → lint/unit → isolated DB integration/contract → dependency and secret scan → web/mobile/container builds → image scan/SBOM/sign → staging deploy → E2E/restore/operational checks → protected manual approval → production. Use OIDC federation/short-lived identity, least privilege, protected environments and immutable digest promotion. Never use mutable `latest` as release identity. Migration is a separate approved one-shot gate. No production auto-deploy is configured.
