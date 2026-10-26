# Quickbuddy Phase 5 final report

Date: 2026-10-26. Status: **merchant workflow slice implemented and backend-verified; Phase 5 Definition of Done not met**.

## Delivered in this slice

- Replaced the preview-only merchant UI with secure login/session restoration, organization/brand/branch onboarding start, authorized branch selection, live dashboard counts, branch availability control, order queue/details, KDS ticket list, product/variant/price create flow, inventory balance/adjustment and explicit unavailable states for settlements, promotions and analytics.
- Added five backend operations: atomic organization/brand/pending-branch onboarding, authorized merchant branch list, branch order queue with item data, branch catalogue read and versioned/audited branch availability switch. Shared PostgreSQL and authorization remain authoritative.
- Updated OpenAPI/API reference. No other app UI was edited for this Phase 5 slice.

## Verification performed

| Check | Result |
|---|---|
| Ruff on touched backend/schema/integration files | Passed |
| Python backend compileall | Passed |
| Backend/unit tests | 40 passed; one upstream Starlette/httpx deprecation warning |
| Targeted merchant workspace test | Passed: branch scoping, queue line data, catalog scope, accept transition, stale version rejection |
| Full integration suite | **30 passed** in 76.70 seconds |
| OpenAPI/API reference | Generated successfully; 118 API operation references |
| Flutter analyze/widget tests/Android build | Not run: Flutter/Dart/Android executables unavailable |
| Screenshots/tablet/real device | Not captured or tested |
| Performance | Not profiled |

## App route inventory

13 route paths: `/` startup, `/sign-in`, `/onboarding`, `/dashboard`, `/orders`, `/orders/:id`, `/kitchen`, `/menu`, `/inventory`, `/promotions`, `/analytics`, `/settlements`, `/settings` (12 distinct screens plus startup routing). See `screen-inventory.md`.

## Blockers

Full KYC/doc upload and approval checklist, push/WebSocket orders, rejection reason, prep estimate, station KDS, pickup verification, full menu editing/modifiers/media, inventory history/batches/thresholds, finance settlements, promotions, analytics, merchant AI, fine-grained staff UI, and Flutter/device verification remain outstanding. See `phase-5-integration-audit.md` and linked feature reports. Do not infer production readiness from backend API tests.

## Startup

From project root, on a Flutter-enabled environment: `cd apps/merchant_app`, `flutter pub get`, then `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000 --dart-define=APP_ENV=development` for Android emulator. For Windows desktop or local web/API routing use the host-appropriate `API_BASE_URL`; production must use HTTPS. This command was documented but could not be run here.
