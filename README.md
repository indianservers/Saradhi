# Quickbuddy

Phase 1 foundation for six independent clients and one shared FastAPI modular monolith.
No business schema, customer records, operational dashboards, payment integration or cloud deployment exists yet.

Start with [DEVELOPMENT.md](DEVELOPMENT.md). Verified results and blockers are in
[docs/operations/phase-1-validation.md](docs/operations/phase-1-validation.md).

Applications: Flutter customer, pilot and merchant; Next.js company administration,
city operations and support. Shared mobile and web UI prevent duplicated application logic.
The public web pages show the application shell; /workspace requires a server-verified
access token and the appropriate role. OIDC sign-in provisioning is a later integration.

Backend: Python 3.12, FastAPI, Pydantic settings, SQLAlchemy 2 async/asyncpg, Alembic,
Redis and ARQ. npm workspaces pin web dependencies in package-lock.json;
requirements.lock pins the verified Python environment. Containers do not include PostgreSQL.

Architecture decisions: docs/decisions/0001-foundation.md. Start Phase 2 only after
reviewing docs/database/schema-design-principles.md and the Phase 2 gate in the validation report.
