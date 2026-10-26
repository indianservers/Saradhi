# Phase 4 test results

Date: 2026-10-26. Environment: Windows workspace; local PostgreSQL `quickbuddy_test` integration target; no Flutter/Dart/Android/iOS toolchain.

| Check | Result | Notes |
|---|---|---|
| `python -m compileall -q backend` | Passed | Backend Python sources compile. |
| `python -m pytest -q backend/tests tests/unit` | Passed: 40 tests | Run inside project `.venv` with workspace on `PYTHONPATH`; one upstream Starlette/httpx deprecation warning. |
| `python -m pytest -q tests/integration` | Passed: 29 tests | Full guarded real-PostgreSQL integration suite. |
| Catalog/cart/quote/payment integration | Passed | Included in 29: live product search, active price and stock, cart version reload, quote lines, signed sandbox simulation, and cross-user cart/payment denial. |
| Multi-merchant checkout integration | Passed | Included in 29: two merchant children, separate fulfillment windows, reservations, and idempotent confirm. |
| Ruff changed backend files | Passed | `routes.py`, `schemas.py`, and integration test file. |
| OpenAPI/API reference generation | Passed | Exported contract and regenerated endpoint reference from FastAPI. |
| `git diff --check` | Passed | Git reported normal LF-to-CRLF working-copy warnings for several existing files. |
| Flutter analyze / widget tests / screenshots | Not run | Flutter/Dart executable is not installed. |
| Android build | Not run | Android/Flutter toolchain unavailable. |
| iOS build | Not run | Windows host has no authorized macOS/iOS toolchain. |
| Development/test sandbox payment API | Passed | Owner-checked completion signs the event server-side and confirms through the idempotent webhook processor; production gateway remains unconfigured. |
| Device tracking map / WebSocket | Not run / unavailable | App polls snapshots; no map key or Flutter WebSocket client is configured. |

These results are limited to checks that ran. They do not establish a complete device-level order/payment/delivery journey. See `phase-4-integration-matrix.md` for remaining API contract gaps.
