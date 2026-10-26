# Multi-brand and multi-branch management

`GET /api/v1/merchant/branches` is the workspace source for the active user. It filters through active organization memberships and current database role assignments with `merchant.write`, including city/branch assignment scope. It does not treat a token role claim or client-side selector as authorization. Queue, catalogue, inventory, availability and state-transition APIs independently validate branch scope.

The app persists the selected branch ID in secure storage and reloads the selected branch from the currently authorized list at dashboard startup. Switching branch changes the queue request and clears the displayed queue before reload. The backend verifies every request even if the local branch ID is tampered with.

Owner onboarding can create a new brand and branch under a selected authorized organization. Full organization rollup, brand management, branch editing/contact/hours/service-area/staff screens, hundreds-branch pagination UI and dedicated organization selector are not complete. Finance-only branch access also awaits corresponding merchant finance contracts.
