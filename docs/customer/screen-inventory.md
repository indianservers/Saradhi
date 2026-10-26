# Customer app screen inventory

The customer app is implemented in `apps/customer_app/lib/main.dart` and uses the shared `flutter_design_system` components. Route definitions are in the same file.

| Route | Live behavior | Honest limitation |
|---|---|---|
| `/` | Loads accepting merchant branches from `GET /api/v1/merchants/branches`; supports pull-to-refresh and error/empty states. | No rating, ETA, offer or merchant image fields in branch API. |
| `/restaurants` | Lists live branch records and opens branch catalogue. | No category filtering in merchant response. |
| `/restaurant/:id` | Loads live priced and in-stock catalogue for the selected branch; user chooses pickup or a saved-address courier option and a future merchant window before adding. | Requires sign-in, inventory, current price and configured future windows. Add-ons are not exposed. |
| `/search` | Debounced `GET /api/v1/catalog/products?q=...` search of current prices and sellable stock. | Requires sign-in; bounded first page only. |
| `/cart` | Loads the persisted customer cart and version, displays branch/product names, updates quantities with optimistic version checks, and deletes lines. | Server cart lines do not include a quoted total until checkout. |
| `/checkout/address-payment` | Gets a fresh server quote, shows its per-line amounts and total, confirms with a quote-scoped persisted idempotency key, and completes a dev/test sandbox intent through the server simulation route. | Production gateway callback remains unconfigured; test simulation has no real-money effect. |
| `/orders` | Loads owned order history from the API. | Reorder and review endpoints are absent. |
| `/orders/:orderId/tracking` | Loads an ownership-checked tracking snapshot every 15 seconds and supports retry after errors. | No configured map tiles or WebSocket client; it displays no synthetic pilot marker. |
| `/orders/:orderId/complete` | Fetches the actual order and status; opens tracking. | “Received” means order record exists; it does not assert payment success or delivery. |
| `/account` | Loads owned addresses, supports manual address creation using active city, freeform text and coordinates, creates support tickets, and revokes session on sign-out. | No geocoder/GPS picker, address edit/delete/default, ticket progress, reviews or favorites API. |
| `/sign-in` | Email/password registration and login. | Phone OTP, password recovery and verification UX are not exposed by backend contract. |

Authentication and personal-resource routes rely on backend authorization. There is no preview fixture path that can be ordered or mistaken for a live product.
