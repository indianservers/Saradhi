# Next.js web application QA

Company Admin, City Operations and Support Console were typechecked and production-built with `npm run typecheck --workspaces --if-present` and `npm run build --workspaces --if-present`. All three Next.js production builds completed successfully.

Routes found per app: `/`, `/login`, `/workspace`, `/api/session`, `/api/backend/[...path]`. No Playwright configuration or browser E2E suite was found, and no screenshots were captured. Login, RBAC navigation, city switching, live dashboard refresh, approvals, dispatch intervention, finance/refund approvals, AI assistant, exports, expiration, tablet layout, overlap and the target mockup comparison were not browser-verified.

Release blocker: run authenticated Playwright journeys against a local API/DB, capture desktop and tablet screenshots, and compare with `Target UI` references.
