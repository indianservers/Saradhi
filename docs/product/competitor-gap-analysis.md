# Quickbuddy competitive feature gap analysis

**Prepared:** 2026-10-27  
**Scope:** Current repository implementation compared with publicly documented Zomato, Swiggy and Blinkit customer/partner capabilities. This is a code-and-documentation audit, not a live competitor-app teardown or a claim that every competitor feature is available in every city. Competitor features, prices and availability change by location and date.

## Implementation update (2026-10-27)

The following P1 customer-discovery and trust gaps were addressed after this audit:

- Customer search now supports bounded branch-name, maximum-price and dietary-code filters; free-text search also matches merchant/brand names.
- Authenticated customers can list their own support cases and read their own chronological conversation. The customer app now shows ticket status and replies without exposing support-agent identifiers.
- Customers can submit one idempotent star rating per delivered order item. Search results expose published average rating and count, and the customer app offers ratings from completed orders.
- Added integration coverage for filter behavior, merchant-name search, verified delivery gating, review retry/cross-customer denial, customer ticket ownership, cross-customer denial and support replies.
- The OpenAPI contract, TypeScript SDK types and API reference were regenerated. After the rating changes, the full local backend/unit/integration run had **123 passed and 5 failed**; all five failures are in existing Telegram bot tests outside this change. The three focused cases for review, discovery and customer support pass. Focused Ruff and workspace TypeScript checks passed. Flutter build/analyzer was not run because Flutter/Dart tooling is unavailable.

This closes only a slice of P1. It does not complete customer ratings/reviews, refunds, mapping, payment activation, or six-app end-to-end verification. P0 items requiring configured Redis/PostGIS, payment credentials, provider setup, database roles and Flutter/device testing remain open until those controls are configured and verified.

## Executive summary

Quickbuddy has a broad shared backend foundation: customer catalogue/cart/quote/order/payment sandbox, merchant order/KDS/inventory paths, pilot assignments/location, company operations, finance, AI and multi-city/category models. Its strongest differentiator in the repository is the ambition to unify food, grocery, retail and local delivery on shared merchant, order and operations infrastructure.

It is **not yet at feature parity as a usable marketplace**. The principal gaps are end-to-end customer and partner workflows, operational service readiness, commercial retention and category-specific fulfillment—not lack of another navigation screen. The Phase 12.C audit explicitly says the product is not ready for a controlled pilot; it records role-coverage and readiness blockers, with Redis-dependent realtime unavailable and mobile/browser E2E unrun. Several app routes are shells or partial flows, and Flutter build/device validation is not evidenced.

### Highest-priority gaps

1. **Complete the first order and delivery loop:** customer address selection, live serviceability, transparent quote/tax/fees, production payment, merchant acceptance/preparation, pilot delivery proof, customer live tracking, cancellation/refund and support recovery.
2. **Make reliability visible and operational:** real-time order/offer updates, road-network ETA/maps, push notifications, reconnection/offline recovery, dispatch automation, and staffed exception resolution.
3. **Build trust and repeat use:** verified ratings/reviews, saved favorites/reorder, reliable search and filters, refunds/complaints, loyalty and a tested membership/benefits proposition.
4. **Make quick commerce real:** store/dark-store inventory by locality, picking/packing, substitutions and consent, partial fulfillment/refunds, expiry/batch controls, capacity/slot SLA and returns. Category labels alone do not create a Blinkit-class operation.
5. **Finish merchant economics and tooling:** promotions, analytics, settlements/payouts, procurement/recipe stock, live POS/printer integrations and staff controls.
6. **Prove the product:** Flutter builds, role-authenticated browser/mobile E2E, accessibility, device performance, realtime/failure/recovery tests and production-like operational drills.

## Evidence and reading guide

- **Implemented** means the repository report describes a working API or app path; it does not imply production activation or mobile E2E verification.
- **Partial** means a real foundation exists, but material workflow pieces, integrations, policy, or UI are missing.
- **Missing** means no verified working capability is documented in the repository for the stated scope.
- **Blocked / unverified** means a required provider, infrastructure service, test environment, or runtime is absent. It is not treated as shipped.

Repository evidence read for this assessment:

- [Phase 3 UI implementation review](../ui/phase-3-final-report.md)
- [Customer Phase 4.A audit](../customer/phase-4a-audit.md), [integration matrix](../customer/phase-4-integration-matrix.md), [final report](../customer/phase-4a-final-report.md)
- [Merchant Phase 5 report](../merchant/phase-5-final-report.md), [Phase 5.A report](../merchant/phase-5a-final-report.md)
- [Pilot Phase 6.A report](../pilot/phase-6a-final-report.md)
- [Admin Phase 7.A report](../admin/phase-7a-final-report.md)
- [Finance Phase 8 report](../finance/phase-8-final-report.md)
- [AI Phase 9 report](../ai/phase-9-final-report.md)
- [Expansion Phase 10 audit](../expansion/phase-10-audit.md)
- [Customer CRM Phase 12.B feature audit](../customer-admin/phase-12b-feature-audit.md)
- [Phase 12.C role-based testing report](../qa/phase-12c-final-report.md)

Competitor references below are official public pages, accessed 2026-10-27. They demonstrate public capability claims/terms, not independent service-level verification:

- [Zomato Gold](https://www.zomato.com/ncr/gold) and [Zomato terms](https://www.zomato.com/policies/terms-of-service/)
- [Zomato online ordering terms](https://www.zomato.com/policies/it/online-ordering/) and [Restaurant Partner dashboard](https://www.zomato.com/partners/)
- [Swiggy business overview](https://www.swiggy.com/corporate/our-business/), [Swiggy One terms](https://www.swiggy.com/terms-and-conditions), and [Swiggy corporate overview](https://www.swiggy.com/corporate/delivering-for-everyone/)
- [Blinkit FAQ](https://blinkit.com/faq), [Blinkit partner opportunities](https://blinkit.com/pages/partner), and [Blinkit terms](https://blinkit.com/terms)

## Competitive capability matrix

| Capability | Zomato | Swiggy | Blinkit | Quickbuddy in this repository | Gap / significance |
|---|---|---|---|---|---|
| Restaurant discovery and delivery | Restaurant discovery, ordering, delivery tracking/payment are part of the documented platform; Gold offers are shown for eligible restaurants. | Food delivery is one of the unified app services. | Not its primary proposition; assortment includes convenience products and prepared/instant food categories. | Live branch/catalogue search, cart, server quote, order creation and order history foundations exist. Search/filter contract lacks merchant ratings, offers, cuisine/diet facets, images and ETA. Customer journey remains partly unverified on Flutter. | **High:** strengthen discovery relevance and complete mobile purchase flow before broadening categories. |
| Quick commerce / grocery | Zomato’s group also surfaces Blinkit separately; not assumed to be equivalent to a food-delivery flow. | Instamart offers groceries/household goods and other categories; corporate pages describe the unified convenience platform. | 7,000+ products in FAQ (site claim), broad daily essentials, locality-specific store availability, delivery estimates, and category-specific complaint/return rules. Partner page describes store, property, seller and delivery-partner paths. | Shared category/catalogue, stock, batch/expiry foundations and pick/pack/KDS foundations exist. Grocery audit says substitution consent, variable-weight billing, missing-item/partial fulfillment and batch/expiry workflow are absent. Phase 10 says not all category UI is present; regulated pharmacy checkout is blocked. | **Critical for Blinkit comparison:** no proven locality-level quick-commerce SLA, full inventory synchronization, substitution/partial refund or fast-store operations loop. |
| Restaurant dine-in / reservations | Gold public pages/terms describe eligible restaurant offers; current terms include delivery and dine-in offers depending on merchant/city. | Dineout lets users discover restaurants, view menus/photos, find seating, reserve and redeem promotions/pay digitally. | Not central; product delivery is the main public proposition. | No verified restaurant table inventory, reservations, dine-in check-in/bill payment or merchant settlement for dine-in. | **High if competing with Swiggy/Zomato:** distinct inventory, reservation and offer redemption workflows required. |
| Membership / savings | Zomato Gold public page advertises eligible free delivery and extra offers; public terms vary by city/merchant/plan. | Swiggy One terms describe select-order delivery benefits, platform discounts and Dineout coupon benefits. | FAQ mentions category offers/instant discounts; no cross-service membership proposition verified in sources reviewed. | Subscription schema and recurring-plan APIs exist, but subscription benefit ledger/eligibility/renewal billing are absent. No customer-facing proven membership savings. | **High retention gap:** design benefits and enforce eligibility, renewal, savings ledger and cancellation/refund policy; do not sell a membership until benefits are executable. |
| Customer trust, feedback, complaint resolution | Customer ratings/reviews and support are part of the platform experience; exact public details vary. | Dineout discovery includes ratings/reviews; unified customer support/One BLCK priority support is publicly described. | Order support, complaint windows, cancellation while packing and category-dependent refund/return terms are publicly documented. | Support ticket creation and feedback tables exist; customer ticket progress/refund status/media are absent. Verified review/rating, moderation workspace and complete customer refund journey are incomplete. | **Critical:** provide status, evidence upload, service-level expectations, resolution and authorized refunds; instrument complaint and recovery rates. |
| Promotions, offers and personalization | Gold and merchant offers; broad discovery and curated listings. | One offers benefits across services; merchant offers, dining promotions and personalized convenience. | Category offers/promotions and time-sensitive availability. | Promotion/discount foundations exist but merchant app promotion workflow and campaign engine/provider are absent; AI currently deterministic, untrained recommendations. CRM audit reports campaigns missing and segments only partial. | **High:** promotion creation, eligibility/stacking, funding attribution, fraud limits, audience consent, experimentation and measured incremental lift. |
| Live order visibility and logistics | Customer order tracking and payment supported in online ordering terms. | On-demand delivery network; Swiggy One BLCK publicly describes faster delivery/on-time guarantee in its press release. | Delivery estimates, service windows and customer updates; FAQ acknowledges delays and support updates. | REST snapshots and 15-second customer polling exist; Redis-backed realtime unavailable locally; no Flutter WebSocket integration or map provider. ETA may be unavailable. Pilot app lacks push/WebSocket recovery and pilot proof-of-delivery flow. | **Critical:** live operations depend on GPS freshness, event delivery, routing, ETA calibration, push and resilient state reconciliation. |
| Dispatch, route and SLA controls | Mature marketplace operation implied by scaled on-demand order and delivery flow; public sources reviewed do not establish exact internal algorithms. | Delivery partner network and faster-delivery programs publicly described; exact dispatch implementation not inferred. | Store cluster / partner delivery model described in FAQ; official partner program includes partner stores and delivery. | Dispatch APIs and deterministic scoring exist; automatic spatial candidate dispatch/replacement offers disabled without PostGIS and durable Redis workers. Road routing, batching, dynamic reroute and measured fairness/SLA are absent. | **Critical:** no automated, benchmarked supply matching/route optimizer or operational SLA evidence. Keep manual fallback and incident escalation. |
| Merchant order and kitchen operations | Restaurant Partner app/dashboard receives real-time orders and menu/order tools described in official partner terms/blog. | Unified restaurant partner program and logistics/tools to grow businesses described on official corporate page. | Seller/store/delivery partner participation and product assortment; dark-store / store partner opportunity. | Merchant queue, order transitions, live catalog and inventory adjustment exist; KDS task/station workflow is implemented and polls every 10 sec. Push realtime, rejection reason, prep estimates, end-to-end pickup, menu modifiers/media and Flutter validation remain incomplete. | **High:** close order-change and exception loops, then add operational realtime and multi-device confirmation. |
| Merchant growth and economics | Restaurant Partner dashboard; marketplace offers and partner onboarding. | Unified partner app approach across offerings; public partner program mentions broader consumer base and delivery network. | Seller product listing and store/property partner paths. | Onboarding core and branch CSV import/export exist. Merchant settlement history/calculation, promotions, analytics, procurement/recipes, transfers, POS/printer live connectors and staff roles are incomplete. | **High:** partner retention requires settlement transparency, commissions/payout predictability and actionable demand/sales reporting. |
| Breadth of local services | Food delivery plus group-level Blinkit and other consumer experiences, depending on app/product. | Unified consumer platform includes food, Instamart, Dineout and other services such as events/Genie as documented by Swiggy. | Extensive daily-needs assortment, with new categories subject to local availability. | Multi-category/city model includes food, grocery, retail, pharmacy category metadata and parcel merchant type. Parcel has no lifecycle; pharmacy is blocked; grocery/retail flows are partial. | **High:** Quickbuddy’s category breadth is more aspirational than complete. Launch only one or two operationally sound categories per zone. |
| Enterprise operations | Public partner dashboards and mature location/marketplace coverage; no internal Zomato control tower feature assumed. | Broad multi-service/city operation; public corporate sources describe app/service portfolio, not the internal admin console. | City/locality operations and partner network; no internal admin parity assumed. | Company admin has city operations, audit/approval and scoped views; no full global order/customer command center, live map/reassignment, multi-city realtime, reports or AI copilot. | **Medium/High for rollout:** operational safety and support tooling must precede city expansion. |

## Detailed Quickbuddy gaps by product surface

### Customer app — launch blockers

**Already present:** email/password auth, saved addresses with manually entered coordinates, live catalogue search, persistent cart, multi-merchant server quote/order structure, sandbox payment path, order history/detail, cancellation contract, tracking snapshot polling and support-ticket creation. Reorder and recurring-plan APIs have limited foundations.

**Missing or partial versus leaders:**

- One complete, verified app journey from address discovery → available assortment → current quote → production payment → merchant acceptance → pilot completion → customer confirmation/refund/support.
- Map-based/current-location address entry, geocoding and clear serviceability result before browsing/checkout.
- Production payment activation and settled/refunded financial correctness. Razorpay is disabled by default; COD/cash custody and settlement are incomplete.
- Real-time tracking UI, map tiles, calibrated road ETA, WebSocket reconnect and push notifications.
- Product modifiers/add-ons, allergens, dietary filters, robust cuisine/brand/rating/offer/delivery-time facets, richer imagery and transparent tax/fee/discount breakdown.
- Customer OTP registration/recovery, phone profile and password reset; order invoices, verified ratings/reviews, favorites, reliable reorder and support ticket status/evidence.
- Partial merchant rejection/unavailability recovery, independent child cancellation/refund and category-specific substitution/missing-item experience.
- Working membership benefits and subscription billing. Existing subscription tables are not a membership product.
- Flutter analyzer/build, physical device, accessibility and target mockup verification have not been performed in this environment.

### Merchant app — partner adoption and revenue blockers

**Already present:** secure session foundation, branch onboarding/selection, dashboard counts, order queue/transitions, catalog price/variant creation, inventory adjustment, KDS with stations and versioned prep tasks, polling and batch-lot read path.

**Missing or partial:**

- Always-on order push/realtime, acceptance/rejection with reason and timeouts, preparation-time commitments, customer/partner communication, outage/offline recovery and reliable pickup handoff.
- Full menu editing: product detail, modifier groups, images, allergens, availability schedules and bulk catalog import.
- Recipe/ingredient-level inventory, purchase orders, supplier/procurement, branch transfer, waste, low-stock alerts and stock reconciliation.
- Promotion authoring and attribution, performance analytics, staffing/role controls and actionable demand forecasts.
- Merchant statements, commission/tax breakdown, settlement approval/payout status, dispute and reconciliation workflows.
- Production POS/printer integrations (current adapters are contracts/stubs), push notifications and phone/tablet Flutter verification.

### Delivery pilot app — fulfillment blockers

**Already present:** pilot identity/session paths, online availability, scoped offers/assignments, atomic acceptance, pickup gating, foreground GPS/location consent, route summaries, earnings read path and incident reports.

**Missing or partial:**

- Pilot-authenticated proof of delivery/OTP, recipient-unavailable and return-to-merchant lifecycle, COD custody and cash reconciliation.
- Push/WebSocket offer delivery, offline action queue/reconciliation and robust app background/OS location behavior.
- Road routing, route polyline, turn-by-turn guidance, live ETA, reliable reroute, multi-order batching and capacity/compatibility controls.
- Shift start/end, break and handover enforcement; payout and incentive dispute workflows; operational incident UI/notifications.
- Automatic spatial dispatch is not enabled locally without PostGIS/Redis worker. No dispatch fairness, speed or service-level benchmark is evidenced.

### Company Admin / CRM — safe scale blockers

**Already present:** city-scoped operations and incident APIs, finance maker-checker slices, branch CSV import/export, scoped customer directory/Customer 360, masked bounded export, segment count preview and audit records.

**Missing or partial:**

- Global cross-city order and customer command center, live rider/map view, assignment reassignment and full exception resolution.
- Governed customer import/merge/profile correction/session revocation, saved segments, RFM/cohorts, funnel/retention analytics, consent-filtered campaigns and A/B experiments.
- Customer privacy request and retention workflows, CRM AI, report builder, large asynchronous exports and broader bulk approvals.
- End-to-end tests exercising every actual database role and all six app UIs. Phase 12.C records NOT READY; only six of 14 discovered roles/contexts were exercised, with critical authorization/readiness/coverage gaps open.

### Quick commerce and multi-category — focus before expansion

A common product/category schema is useful but does not provide category parity. Before claiming grocery/quick commerce, Quickbuddy needs:

- Store/dark-store selection and assortment by exact locality; inventory freshness and reservation across picker/checkout races.
- Picking/packing task assignment, substitutions with customer consent, weighted-product price authorization, unavailable-item changes, partial completion and line-level refunds.
- Batch/expiry, recalls, quality checks, temperature handling where relevant, replacement/return rules and category-specific support windows.
- Store capacity, picking throughput, courier capacity, a realistic SLA promise, cutoff/operating hours and exception playbooks.
- Pharmacy additionally needs prescription intake, pharmacist review, controlled-category safeguards and jurisdiction-specific operations; current regulated checkout is correctly blocked.
- Parcel additionally needs sender/recipient, package dimensions/weight, prohibited-item validation, pricing, pickup/drop-off proof and failed-delivery/return workflows; these are absent.

## Priority and sequencing recommendation

| Priority | Workstream | Why now | Exit criteria before calling it done |
|---|---|---|---|
| P0 | Pilot readiness and customer-to-delivery vertical slice | Current QA report says NOT READY; broken order loop undermines every comparison. | Redis/PostGIS or supported equivalent configured; assigned roles covered; customer payment, merchant accept/prep, pilot OTP/proof, tracking, cancellation/refund/support all pass authenticated E2E for two companies/cities as applicable; device build verified. |
| P0 | Payments, finance and recovery | Sandbox-only checkout and incomplete cash/refund/settlement controls block real commerce. | Provider test/live approval; payment webhook/reconciliation and ledger invariants; COD custody if offered; merchant/pilot payable, settlement, refund and dispute audit trail; failure/retry idempotency evidence. |
| P1 | Customer discovery and trust | Leaders compete on selection, relevance, reliability and confidence. | Search facets and merchant/product data; serviceability/address UX; verified order feedback; ticket status and resolution; invoice and clear fee/tax/refund rules; accessibility and usability QA. |
| P1 | Merchant and pilot operational realtime | Polling and incomplete exception workflows impede SLA and partner trust. | Push/realtime with snapshot recovery; accept/reject/prep/pickup/delivery exception state machine; delivery proof; online/offline recovery and operational dashboards. |
| P1 | One differentiated loyalty proposition | Membership can improve repeat frequency, but only with auditable benefits and economics. | Explicit eligible services/merchant thresholds; benefit/savings ledger; renewal/payment/cancel/refund; caps/abuse controls; cohort and incremental retention measurement. |
| P2 | Focused grocery/dark-store pilot | Broad categories without pick/pack and substitution processes increase refunds and safety issues. | One locality pilot with reliable inventory, substitution consent, partial refund, batch/expiry, measured pick/pack and delivery SLA. |
| P2 | Dine-in, corporate, parcel, pharmacy, and broad admin CRM | Each is a separate operational product with distinct integrations and compliance needs. | Separate acceptance criteria, owner, operating process and audit; do not infer readiness from shared schemas. |

## Metrics Quickbuddy should instrument before comparing outcomes

- Customer: address-to-serviceable rate, search-to-product conversion, checkout completion, payment success, first-order completion, repeat within 30/60 days, cancellation/refund, complaint rate and support resolution time.
- Delivery: offer response, assignment time, pickup wait, promised-vs-actual ETA, on-time delivery, GPS freshness, failed delivery, safety incident, cost per delivery and pilot earnings accuracy.
- Merchant: order acceptance, prep-time accuracy, item unavailability, cancellation, stock accuracy, settlement aging, promotion incrementality and partner retention.
- Quick commerce: item fill rate, substitutions accepted, picking/packing time, weighted-item adjustment, partial refund time, waste/expiry and SLA by locality/time block.
- Platform: API p95/p99, realtime fanout delay/reconnect, payment reconciliation drift, authorization denials, incident response, crash-free sessions and app launch/frame performance.

Do not claim competitor-level speed, uptime, geographic coverage or operating scale until measured on representative production-like traffic and a defined locality cohort. Blinkit’s FAQ currently states that over 70% of its deliveries are within 15-minute timelines; this is its own published claim, not an independent benchmark or a target Quickbuddy should promise without operational data.

## Bottom line

Quickbuddy has meaningful shared-platform foundations and some real backend workflows, but its current evidence describes a **partial product foundation rather than a Zomato/Swiggy/Blinkit-equivalent consumer and operations ecosystem**. The most important missing feature is a proven, reliable end-to-end service loop. Finish that loop, close payments and exception handling, validate every app on real runtimes, then launch one locality/category at a time. Add membership, dine-in, campaigns and additional categories only when their operational and financial workflows are executable and measurable.
