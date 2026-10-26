# Customer UX flow analysis

Date: 2026-10-26. Counts below are route/action counts derived by reading the implemented flow, not interaction telemetry or observed device taps. Counting conventions: one tap means one explicit customer activation; typed text/scrolls and system permission prompts are excluded. Flutter execution was unavailable.

## Primary order journey

| Journey | Existing Phase 4 path (code estimate) | Phase 4.A path (code estimate) | Conditions / remaining input |
|---|---:|---:|---|
| Returning customer, previously used this merchant, saved valid address/method/window | Home → merchant (1), add (2, bottom sheet every time) → cart (3) → quote (4) → confirm (5) | Home → merchant (1) → quick-add (2) → sticky cart/checkout (3) → confirm (4) | Backend still revalidates quote; explicit final confirmation retained. No device telemetry. |
| First order or invalid/missing saved preference | Home → merchant (1) → add (2) → choose method/address/window and Add (3–5) → cart (6) → quote (7) → confirm (8) | Same choice sheet and required selections; after adding, cart/checkout path is 3 further activations. | Selection count varies with pickup/courier and whether address exists. A no-address courier choice is not offered. |
| Reorder | No working reorder route was available in customer surface | Orders → Add items again → review cart → quote → confirm (4 activations after opening Orders) | Items use current available variants and first returned future window; unavailable/address-invalid rows are skipped, and customer must review. |

The one-tap improvement is specifically the add-to-cart control when all saved choices still match current backend data. It does not mean one-tap order placement or payment. The choice sheet remains when validation fails or preferences are absent.

## Navigation and friction

- Shared `CustomerShell` provides Home, Search, Orders and Account navigation on customer routes, hidden during onboarding and sign-in.
- A branch menu’s sticky cart bar routes directly to checkout. The regular cart remains available for grouped quantity review.
- Address choice is on Home; address and method cannot currently be edited on a cart line after it is created. Rebuilding the line is the current workaround.
- Search filters cover merchant type only. Cuisine, price, rating, brand, dietary needs, offers and time require new backend query support.
- Reorder adds eligible items to cart but does not skip current quote/confirmation.

## Flow states to exercise on device

Run signed-out/signed-in, empty/nonempty cart, valid/stale saved address, valid/stale window, quote expiry, API timeout, version conflict, merchant out of stock, pending sandbox payment and resumed payment. The unit/integration evidence does not exercise Flutter rendering, navigation gestures or touch count.
