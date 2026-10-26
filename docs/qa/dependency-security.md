# Dependency and supply-chain review

- `npm audit --json`: 0 vulnerabilities reported across npm lockfile dependencies (info/low/moderate/high/critical all zero) at assessment time. `npm audit --omit=dev --json`: same result.
- `pip-audit -r requirements.lock`: no known vulnerabilities reported. Syft, Trivy, Grype, Gitleaks and OSV-Scanner were not installed. Therefore container vulnerability status, SBOM generation, and secret history scanning are **not verified**.
- `requirements.lock` pins Python versions; `package-lock.json` provides npm resolution. Docker base is `python:3.12-slim`; Redis Compose image is `redis:7.4-alpine`. Image digest pinning and image scan were not verified.
- CI now runs Python `pip-audit` and npm `npm audit --audit-level=high` alongside existing Ruff/pytest/format/type/build/contract/migration checks. SBOM, historical secret scan, container scan, Flutter, browser E2E, and load gates remain absent.

Do not interpret npm audit zero as a full software supply-chain pass. Add Python and container scanners, secret scanning on current and historical commits, generated SBOM artifact, and a controlled dependency-update process with compatibility tests.
