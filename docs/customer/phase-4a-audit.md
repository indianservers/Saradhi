# Phase 4.A customer app audit

Audit date: 2026-10-26. Scope: customer Flutter app, shared Flutter networking, customer-facing API routes, schemas and PostgreSQL integration tests. Pilot, Merchant and Company Admin UIs were not part of this phase. The workspace has no Flutter/Dart or Android SDK, so source edits are not equivalent to a verified mobile build.

## Screen inventory

The visual references are `Target UI/quickbuddy_everything_delivered_happier.png` and `docs/ui/reference-crops/customer-01.png` through `customer-10.png`. The board is a design reference, not a screenshot of this build. “Implemented” below describes code-path inspection; backend verification is called out separately.

| Reference / screen | Implementation and navigation | Data, states and validation | Audit classification |
|---|---|---|---|
| 01 Onboarding | `/onboarding`; skip/get started/sign-in; shared photo asset, solid caption panel | Static copy/assets; no network. Sign-in destination is functional by route. | Implemented; visual comparison/build unavailable. |
| 02 Home | `/`; persistent shell nav; delivery selector, search, categories, nearby branches, recommendations, active order | Live public branches first; address, active order and deterministic suggestions load independently for signed-in users. Has branch skeleton/error/empty. Address failure does not block public discovery. | Backend-backed sections present; not Flutter verified. Reorder/recently visited and AI concierge absent. |
| 03 Merchant discovery | `/restaurants`; branch pagination and merchant cards | Live public accepting branches; loading, retry and empty states. | Implemented; pagination source inspected, no widget/device verification. |
| 04 Merchant menu/product | `/restaurant/:id`; authenticated live catalogue, stock/price and add flow | Product list loading/error/empty; add obtains backend future windows and saved addresses; quick-add only if saved method/window and required address are still present, otherwise asks. Quote revalidates. No product details/addons API. | Core catalogue/add implemented; modifiers, ingredient/allergen detail and product gallery blocked by API. Flutter verification unavailable. |
| 05 Universal search | `/search?type=...`; type chips, 300ms debounce, request cancellation, cursor | Authenticated current-price/current-stock catalogue endpoint; empty/clear/retry states. | Product search implemented; merchant-name/cuisine/brand/diet/rating/offer/time filters unavailable in catalogue contract. Not Flutter verified. |
| 06 Cart | `/cart`; compact expandable branch groups, quantity controls, delete, single checkout action | Secure cart ID; reloads owner-scoped cart version/lines; quantity sends expected version; API errors surface. | Multi-merchant cart path implemented; fees/tax/discount display limited to quote contract. No Flutter test run. |
| 07 Address/payment/checkout | `/checkout/address-payment`; quote groups merchants and displays server line/total, explicit final sandbox confirmation | Quote API checks current server rules. Production gateway unavailable; development/test sandbox only. Saved address is chosen while adding a line; checkout cannot edit it. | Sandbox path backend-verified; payment is not production-ready. No Flutter build/run. |
| 08 Schedule/multi-merchant | `/checkout/schedule` aliases same checkout; one selected future window per line, per-merchant groups | Windows are fetched from branch API and quoted/revalidated. Separate deliveries are disclosed. | Multiple merchant windows and parent/child split backend integration verified. ASAP, recurring orders, multi-address-per-merchant editing and independent child-order cancellation UX incomplete. |
| 09 Tracking | `/orders/:orderId/tracking`; 15-second authenticated snapshot polling, retry, support shortcut | Retains last snapshot and labels it after failed poll. No simulated movement. | Ownership/polling code inspected; backend tracking authorization exists. Flutter WebSocket, map, route, ETA UI and reconnection stream unimplemented/unverified. |
| 10 Complete/review/reorder | `/orders/:id/complete`, `/orders`; payment status/recovery, history, add-items-again | Owned order/payment/reorder-line APIs; current address/window/stock checked on cart add; user reviews current quote before confirming. | Backend reorder/payment ownership test passed. Ratings, pilot reviews, partial cancellation/refund endpoints absent. |
| Account/address/support (no dedicated board crop) | `/account`; manual city/address/coordinates, support ticket/message, logout | Address list/create and server-side field validation; ticket creates actual ticket/message; local credentials clear even when revoke call fails. | Implemented with backend endpoints; no geocoder, edit/delete/default address, customer ticket progress or refund request API. Flutter form validation/semantics unverified. |
| Sign-in | `/sign-in`; email/password register/login | Form email check and 12-character registration minimum; secure token store, refresh retry and logout integrations in shared networking. | Backend auth integrations exist; phone/OTP customer registration, password recovery and terms flow unavailable. Widget/device verification unavailable. |

## Cross-screen checks

- **Working and backend verified:** current catalogue filtering; cart persistence/version read; quote enrichment; sandbox completion/recovery contract; owner checks for cart, payment, reorder and order resources; multi-merchant parent/child confirmation and idempotency. Evidence: `tests/integration/test_vertical_slice.py` and current run recorded in `phase-4a-final-report.md`.
- **Implemented, mobile verification blocked:** new customer UI states and routes, preference-aware quick-add, persistent nav, search cancellation, grouped cart/quote, retry/reorder and tracking polling. No Flutter SDK is installed, so no analyzer, widget, golden, emulator or device result is claimed.
- **Incomplete/API blocked:** payment gateway and stored payment preference; modifiers/addons, advanced search facets, fees/tax/discount breakdown, editable delivery options after add, customer rating/favorites/ticket progress/refund request, full live map/ETA/WebSocket, operational AI concierge/actions, OTP and geocoding.
- **Responsive/accessibility:** labels/tooltips and some category semantics exist. Small/large viewports, enlarged text, screen reader, keyboard/focus, contrast and touch-target review require running Flutter and remain open.

## Defect corrections in this audit

- Added owner-scoped cart state and catalogue/reorder/payment recovery API contracts used by the customer flow; live pricing/stock is not inferred from UI state.
- Corrected stale widget-test copy to current home copy (test itself could not run).
- Added saved-preference quick-add only when a fetched current branch window and the saved method/address remain valid; the final order confirmation stays an explicit customer action.
- Replaced onboarding gradient caption with a solid panel.
- Regenerated OpenAPI and API reference after route/schema updates.

## Current blocking items

Install/use a Flutter-enabled environment to run `flutter analyze`, widget tests, Android build and three viewport captures. Then connect a configured map/realtime client, production payment provider, and the missing customer APIs before asserting full Phase 4.A completion.
