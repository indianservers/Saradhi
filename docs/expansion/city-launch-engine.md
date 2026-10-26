# City launch engine

New cities created by `POST /api/v1/geo/cities` begin inactive and stay out of customer city/catalog queries. Configure active zones and enabled zone categories, then inspect `GET /api/v1/operations/cities/{id}/readiness`. A platform user with `geo.write` can activate only when the city has an active zone, enabled category and at least one approved accepting branch with a non-regulated active product, current branch price, sellable stock, active pickup capability and future capacity. Activate and suspend operations are audited. Regulated categories cannot be enabled.

This is the backend safety/activation slice, not the requested multi-step Company Admin wizard. Launch configuration version history, operating-calendar setup, city manager assignment, boundary drawing, pricing/support/payment configuration and phased zone rollout UI remain incomplete.
