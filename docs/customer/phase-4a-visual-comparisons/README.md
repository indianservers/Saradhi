# Phase 4.A visual comparison evidence

Date: 2026-10-26. Source reference: `Target UI/quickbuddy_everything_delivered_happier.png`; numbered customer crops: `docs/ui/reference-crops/customer-01.png` through `customer-10.png`.

| Crop | Reference role | Customer route | Source inspection | Implemented screenshot / pixel comparison |
|---|---|---|---|---|
| 01 | Onboarding | `/onboarding` | Inspected; image + solid caption panel and CTA | Not captured: Flutter/Dart runtime unavailable |
| 02 | Home discovery | `/` | Inspected; address/search/categories/promotion/nearby and active-order states | Not captured |
| 03 | Merchant discovery | `/restaurants` | Inspected; branch list and pagination | Not captured |
| 04 | Merchant menu/product | `/restaurant/:id` | Inspected; current catalogue, availability and add-choice flow | Not captured |
| 05 | Search/filter | `/search` | Inspected; product search/type filters/empty state | Not captured |
| 06 | Cart | `/cart` | Inspected; merchant groups and quantity/remove controls | Not captured |
| 07 | Address/payment | `/checkout/address-payment` | Inspected; authoritative quote and explicit sandbox action | Not captured |
| 08 | Schedule/multi-merchant | `/checkout/schedule` | Inspected; same quote screen with per-line windows | Not captured |
| 09 | Tracking | `/orders/:orderId/tracking` | Inspected; status snapshot and honest map placeholder | Not captured |
| 10 | Delivered/reorder | `/orders/:id/complete`, `/orders` | Inspected; order/payment status and add-items-again | Not captured |

No screenshot is fabricated from the target board. These are source-level comparisons only; spacing, system insets, text scaling, overflow, image crop and pixel fidelity remain unverified. Capture app/device images for each route and loading/error/empty states on Flutter-enabled hardware before recording a visual pass.
