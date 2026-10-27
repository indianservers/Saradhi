# Quickbuddy Pilot App

Pilot client for the shared Quickbuddy API. Connected flows include email/password authentication, limited city-based pilot profile setup, server-authoritative availability, foreground location reporting, live assignment polling, accept/reject, pickup confirmation, adaptive foreground location requests, source-attributed route ETA when available, authorized-zone demand advisories, pilot shift context, external map launch, and pilot earnings ledger reads.

## Local setup

Android, iOS and web platform runners are included. Install Flutter with Dart `>=3.9`. If runners are missing, initialize them from the repository root:

```powershell
./tools/dev.ps1 flutter-init -App pilot_app
./tools/dev.ps1 mobile -App pilot_app
```

The initializer creates Android/iOS/web runners only if absent, installs packages, analyzes, and tests. For an Android emulator, run from this directory:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

For a browser/local backend use `--dart-define=API_BASE_URL=http://localhost:8000`. Production builds require HTTPS:

```powershell
flutter build apk --dart-define=APP_ENV=production --dart-define=API_BASE_URL=https://api.example.com
```

The initializer requests Android foreground coarse/fine location and iOS `WhenInUse` disclosure. The app does not request background tracking. Configure secure-storage backup exclusions before release.

## Backend limitations

The pilot API exposes read-only active/next shift and authorized-zone/capability context. Pilots can submit typed operational incident reports; authorized city staff can review, acknowledge, and resolve them through the API. A dedicated staff UI and atomic incident-to-task handover are not available. Shift scheduling, break administration, end-of-shift safeguards, pilot-side delivery proof, COD, optimized multi-stop batches, payout state, push/WebSocket offer feeds, and in-app road routing are also unavailable. Demand bands are advisory outputs of the deterministic untrained baseline. Location request settings are more frequent during accepted/picked-up work and reduced while online idle; physical battery impact is not measured. See the [Phase 6 audit](../../docs/pilot/phase-6-audit.md) and [Phase 6.A audit](../../docs/pilot/phase-6a-audit.md).

## Physical Android QA

With the local backend running and USB forwarding enabled (`adb -s <serial> reverse
tcp:8000 tcp:8000`), run from this app directory:

```powershell
flutter test integration_test/device_flows_test.dart -d <serial> --dart-define-from-file=../../.secrets/device-pilot.json
```

Supply `API_BASE_URL`, `QA_EMAIL`, and `QA_PASSWORD` in that ignored JSON file, using
the local synthetic pilot. The device suite signs in and opens each operational screen.
It does not claim a completed delivery, real GPS journey, payout, or provider integration.

The incident test submits a synthetic vehicle-breakdown report, which intentionally puts
the demo pilot into the backend safety hold. Acknowledge and resolve that report through
the authorized local operations API, then restore the pilot offline before availability QA.
`integration_test/availability_test.dart` exercises foreground location and the online/offline
switch; approve Android's foreground location prompt on the test device. It distinguishes
a successful online transition from location failure recovery. A full delivery run still
requires dispatch-created offers and a serviceable courier order.

In-app audio calling is available for active assigned deliveries. See
[calling setup and background limits](../../docs/customer/in-app-calling.md).
