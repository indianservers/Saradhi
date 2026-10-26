# Phase 7 integration audit

## Scope and result

This implementation connects the three Next.js apps to the shared FastAPI backend through a server-side session and an allowlisted same-origin proxy. It delivers live city dispatch snapshots, aggregate fleet status, pilot incident acknowledgement/resolution, approved branch listings, registered AI model versions, and a claim-based support ticket workflow.

It is a production-oriented vertical slice, not completion of the full Phase 7 brief. The audit found no authorized endpoints for most requested modules; those screens are not represented by sample data.

## Existing apps and contracts

| App | Route | Role gate | Connected work |
| --- | --- | --- | --- |
| Company administration | `/workspace` on port 3000 | `company_admin`, `platform_super_admin` | City dispatch, fleet aggregates, pilot incidents, approved branches, AI registry |
| City operations | `/workspace` on port 3001 | `city_operator`, `city_manager`, `platform_super_admin` | City dispatch snapshots and incident acknowledge/resolve |
| Support console | `/workspace` on port 3002 | `support_agent`, `platform_super_admin` | Ticket inbox, claim, conversation, reply, resolve |

All three apps use `/api/session` for login/logout and `/api/backend/*` for narrowly allowlisted API calls. Access and refresh tokens remain in HTTP-only cookies. The backend remains authoritative for identity, city scope, ticket ownership, and state transitions.

## API gaps found

The current backend does not expose safe administration endpoints for country/city/zone management, merchant approval, pilot KYC and roster administration, customer directory/privacy requests, order command-center snapshots, GPS map data, dispatch reassignment, refund approval queues, finance reporting, pricing policies, user/role management, WebSocket subscriptions for these consoles, or alert ownership. The UIs report missing capabilities rather than fabricating records.

## Migrations and contract updates

- `20261026_0013`: support ticket assignee reference and index.
- `20261026_0014`: permits only the dedicated `support_agent` role to receive a central support queue assignment without an organization scope.
- `20261026_0015`: supports explicit city-only assignments for `city_manager` and `city_operator`; `/operations/authorized-cities` returns only cities passing the backend dispatch scope check.
- OpenAPI JSON and generated TypeScript schema were regenerated after route changes.

## Commands

From the repository root: `npm run dev --workspace @quickbuddy/company_admin`, `npm run dev --workspace @quickbuddy/city_operations`, and `npm run dev --workspace @quickbuddy/support_console` (ports 3000, 3001, 3002). Apply schema updates with the repository's normal Alembic upgrade command before deploying.
