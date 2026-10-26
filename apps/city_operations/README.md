# City operations
From the monorepo root: `npm ci`, then `npm run dev -w @quickbuddy/city_operations`.
Build: `npm run build -w @quickbuddy/city_operations`. Serve: `npm run start -w @quickbuddy/city_operations`.
Uses port 3001. Copy `.env.local.example` to `.env.local` in this app to override server API URL.
`/` is a public shell containing no operational data. `/workspace` checks the real API identity and `city_operator` role on the server; unauthenticated access redirects to `/login`.
OIDC callback, refresh lifecycle and provisioning are intentionally not implemented. No login bypass or default account exists.
Shared UI and network types come from workspace packages. Module links remain explicitly planned until their routes and authorization policies exist.
