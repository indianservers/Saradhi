# Merchant app screen inventory

Date: 2026-10-26. Reference: `Target UI/quickbuddy_restaurant_partner_app_showcase.png` and its 10 labeled phone panels. Route count: 13 including startup; distinct screens: 12.

| Ref | Route / screen | Current source behavior | API/state classification |
|---|---|---|---|
| 01 | `/` startup → `/sign-in` or `/dashboard` | Restores existing secure session; otherwise sign-in. | Session presence checked; no Flutter execution. |
| 01 | `/sign-in` | Validated email/password login; account creation toggle. | `/auth/register`, `/auth/login`; saves returned access/refresh tokens securely. |
| Onboarding | `/onboarding` | Create organization or select authorized organization; create brand/branch and submit. | Cities, `/merchant/branches`, `/organizations`, `/merchants/brands`, `/merchants/branches`; branch remains pending. KYC gaps are disclosed. |
| 01,10 | `/dashboard` | Branch picker, live queue counts, audited availability switch, actions. | Authorized branch/queue endpoints; refresh action and 15-second queue poll. |
| 02 | `/orders` | Status chips and branch-scoped queue. | Queue polling every 12 seconds; retry/loading/empty. |
| 03 | `/orders/:id` | Order lines and allowed transition for current status. | Loads selected branch queue; expected-version transition. No customer PII exposed. |
| 04 | `/kitchen` | Active backend tickets, refreshed every 10 seconds. | Branch queue; no auto-completion. No station or sound API. |
| 05 | `/menu` | Branch product and variant listing; create product/variant/price. | Merchant catalogue and existing catalog/price APIs. Partial create possible if a later API step fails. |
| 06 | `/inventory` | Current on-hand/reserved/sellable stock and adjustment dialog. | Existing branch read/adjust endpoints. No ingredient BOM assumptions. |
| 07 | `/promotions` | Explicit unsupported-feature state. | No merchant campaign API. |
| 08 | `/analytics` | Explicit unsupported-feature state. | No merchant analytics aggregate API. |
| 09 | `/settlements` | Explicit unsupported-feature state. | No merchant settlement summary/history API. |
| 10 | `/settings` | Selected branch status, clear limits, sign-out. | Branch switch/availability through dashboard. Hours, bank, staff and payout controls not exposed. |

Shared shell uses snow-white surface, violet selected navigation, orange primary action, reusable `QbBrand`, `QbPrimaryButton`, `QbStatusChip`, `QbPanel`, and explicit notice/error panels. Flutter screenshot, text scaling, overflow, tablet and assistive-technology checks remain unverified.
