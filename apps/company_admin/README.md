# Company administration
From the monorepo root: `npm ci`, then `npm run dev -w @quickbuddy/company_admin`.
Build: `npm run build -w @quickbuddy/company_admin`. Serve: `npm run start -w @quickbuddy/company_admin`.
Uses port 3000. Copy `.env.local.example` to `.env.local` in this app to override server API URL.
`/` is a public shell containing no operational data. `/workspace` checks the real API identity and `company_admin` role on the server; unauthenticated access redirects to `/login`.
OIDC callback, refresh lifecycle and provisioning are intentionally not implemented. No login bypass or default account exists.
Shared UI and network types come from workspace packages. Module links remain explicitly planned until their routes and authorization policies exist.
