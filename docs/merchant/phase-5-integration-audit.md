# Phase 5 Merchant App integration audit

Audit date: 2026-10-26. Target reference: `Target UI/quickbuddy_restaurant_partner_app_showcase.png`. Scope is `apps/merchant_app` and merchant-scoped routes using the existing Quickbuddy PostgreSQL/backend. Customer, Pilot and Admin app UIs were not changed. Flutter/Dart and Android executables are absent, so no mobile analyzer/build/render result is claimed.

## Findings and classifications

| Capability | Status | Evidence / current behavior |
|---|---|---|
| Merchant login | Implemented; backend contract verified, Flutter unverified | Email/password login uses shared secure token store and refresh transport. App now saves token response and restores session at startup. No merchant-specific OTP or password reset. |
| Merchant onboarding | Incomplete / backend blocked | App creates organization, brand and branch; branch remains pending until an authorized reviewer acts. Existing API does not collect KYC/document uploads, bank/tax/FSSAI data, contact/address/hours/photos, or complete checklist state. No approval is granted by the app. |
| Organizations/brands/branches | Partially working | Authorized branch list and branch selector support scoped branches; onboarding can add another branch under a selected authorized organization. No organization-level consolidated view or branch edits. |
| Dashboard | Implemented against live queue | Displays selected branch and actual pending/accepted/preparing/ready counts from branch queue; low-stock and sales KPIs not fabricated. Accepting-orders switch calls audited versioned backend API and is disabled until approval. |
| Incoming orders | Implemented; backend verified | New branch-scoped queue returns child orders and line items; refresh every 12 seconds, retry, details and expected-version state changes through existing commerce transition. No WebSocket/push notification/background alert. |
| Order actions | Partial | Accept, start preparation and mark ready work through backend transitions. Reject reason, editable prep estimate, pickup handover verification, customer notes/customizations are not in current contract. |
| KDS | Partial | Branch queue grouped into active tickets; manual milestone controls in order details. No stations, per-item readiness, sound alerts, timed escalation or tablet screenshot testing. Timer never auto-completes work. |
| Catalogue | Partial | New branch-scoped catalogue read shows product/variant, active branch price and stock (including unpriced/out-of-stock rows). Add flow creates product + variant + INR price via existing write APIs. Edit, images, modifiers, tax, dietary attributes, availability scheduling and rollback of partially completed multi-call create are not supported. |
| Inventory | Partial | Existing branch-authorized stock read/adjustment is wired; adjustment uses unique idempotency key and actor attribution. API locks stock and rejects below-reservation quantity. Product labels, reason codes, history UI, low-stock policy UI and batch/expiry UI remain absent. |
| Branch availability | Implemented; integration verified | Added branch-scoped, expected-version switch and audit record; cannot activate unapproved branch. No holiday, busy mode, acceptance limits or operating-hours editor. |
| Settlements / finance | Blocked by merchant API | No branch-scoped settlement history/summary endpoint. App shows a clear unavailable state; no mock payout values. |
| Promotions | Blocked by backend | No merchant campaign endpoints; no decorative active controls. |
| Analytics | Blocked by backend | No merchant analytics aggregate; no invented charts/growth values. |
| AI assistant | Incomplete | Existing AI inference/recommendation surfaces are not a scoped merchant copilot. No merchant AI action is exposed. |
| Staff roles / KYC / notification / handover | Incomplete | Database permissions and some workflows exist, but no complete app screens or push/socket subscription. No bank/KYC data is surfaced. |
| Visual verification | Blocked by toolchain | Ten reference phone panels are mapped in `phase-5-visual-comparisons.md`; no Flutter screenshot, pixel match or tablet capture was possible. |

## Shared-backend additions in this phase

- `POST /api/v1/merchant/onboarding`: atomically creates an organization (or validates an existing organization scope), brand and pending branch; no app-side approval.
- `GET /api/v1/merchant/branches`: lists branches only where the authenticated active member has a current `merchant.write` assignment scoped to that organization/city/branch.
- `GET /api/v1/merchant/branches/{branch_id}/orders`: branch-authorized child queue with item snapshots; no customer private address/name is included.
- `GET /api/v1/merchant/branches/{branch_id}/catalog`: branch-authorized product/variant/current price/stock view, including unavailable rows.
- `PUT /api/v1/merchant/branches/{branch_id}/availability`: version-checked and audited accepting-orders update; unapproved branches cannot be opened.
- Existing `POST /merchant-orders/{child_id}/transition`, catalogue write, inventory read/adjust and auth APIs are consumed by the app.

## Verification status

The latest backend integration run and exact counts are in `phase-5-final-report.md`. Flutter analysis, widget execution, Android build, screenshot, real device and performance profiling were unavailable. This audit is not a production-readiness claim.
