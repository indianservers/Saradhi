# Phase 5 merchant visual comparisons

Reference reviewed: `Target UI/quickbuddy_restaurant_partner_app_showcase.png` (10 labeled phones). The reference defines orange/violet/white brand, compact operation cards and clear order states.

| Ref panel | Screen | Implementation comparison | Screenshot/device result |
|---|---|---|---|
| 01 | Sign-in/dashboard | Secure sign-in and actual branch dashboard replace sample metrics. | Not captured; Flutter toolchain absent. |
| 02 | Live orders | Branch-scoped queue with backend state chips and explicit refresh cadence. | Not captured. |
| 03 | Order preparation | Real order details/line items and allowed state transitions; no fictional customer name/time. | Not captured. |
| 04 | Kitchen display | Active backend tickets and manual order detail actions; no fake timers/stations. | Not captured. |
| 05 | Menu management | Current branch catalogue and product-create action. | Not captured. |
| 06 | Inventory | Real on-hand/reserved balances and adjustment dialog. | Not captured. |
| 07 | Promotions | Backend-blocked message; no decorative campaign rows. | Not captured. |
| 08 | Analytics | Backend-blocked message; no sample graph/revenue. | Not captured. |
| 09 | Settlements | Backend-blocked message; no sample balance/payout history. | Not captured. |
| 10 | Branch/profile settings | Authorized branch selector/availability and explicit unsupported settings. | Not captured. |

No target pixels were reused as screenshots. No rendered capture, spacing comparison, small-screen overflow pass or tablet KDS pass is claimed because Flutter/Dart and Android tooling are not installed in this environment. Capture each implemented route and loading/empty/error state on an available Flutter device before recording visual fidelity as passed.
