# Phase 6 pilot app audit

Audit based on the Phase 6 request and repository state before this work, plus the changes made in this tree. Backend remains the shared system of record.

| Capability | Evidence before work | Current result |
|---|---|---|
| Routes and UI | `apps/pilot_app/lib/main.dart` contained static preview states | Replaced with sign-in/setup, live offers, assignment, pickup, route, earnings and profile flows. |
| Identity | Shared `POST /auth/login`, refresh interceptor, secure token store | Email/password sign-in and optional account creation now save server tokens. OTP login is not configured in current client. |
| Pilot onboarding/KYC | `POST /pilots` accepts city only; no document/vehicle/contact/payout capture APIs | City profile setup connected. KYC/document approval remains operations-only; full onboarding blocked by backend contract. |
| Dispatch offers | Offer creation, acceptance and rejection APIs existed; no pilot-owned list API | Added `GET /pilots/me/assignments`, scoped from token identity. Acceptance remains atomic in shared logistics service. |
| Assignment details | Shared order/branch/fulfillment models | Assigned pickup and item data returned; exact drop-off snapshot is withheld until offer acceptance. |
| GPS | Authenticated consent and GPS ingestion already existed | Added foreground Geolocator capture, accuracy filtering, persistent sequence, visible consent and online polling/stream. No background tracking. |
| Pickup | `POST /delivery-tasks/{id}/pickup` and backend readiness guard existed | Connected versioned pickup action, enabled only when merchant order is ready. |
| Delivery completion | `acknowledge` requires customer identity; no pilot OTP/proof upload endpoint | Pilot completion intentionally unavailable. A failed-delivery report calls existing generic failure transition. |
| Routing | ETA service/provider abstraction exists; no configured map SDK contract in this app | External maps URL fallback uses backend coordinates. No in-app route polyline or turn-by-turn claims. |
| Earnings | Immutable `fulfillment.pilot_earnings` records exist, no pilot read API | Added pilot-scoped read API and ledger screen. No payout state, wallet, or fabricated totals. |
| COD, shifts, support, notifications | No pilot-facing operational APIs found | Not implemented. Offers/assignments poll the backend; push/WebSocket feed is not available to this client. |
| Security | Existing task acceptance/progress derives pilot ownership from authenticated actor | Added own-profile and own-assignment reads. Cross-pilot isolation covered in real PostgreSQL integration flow. |
| Native configuration | No platform runner was checked in; Flutter/Dart unavailable locally | Added Geolocator/URL launcher dependencies and updated `flutter-init` to request foreground-only OS location permissions. No build/device validation. |

See [final report](phase-6-final-report.md) for acceptance gaps and [security tests](security-tests.md) for what was exercised.
