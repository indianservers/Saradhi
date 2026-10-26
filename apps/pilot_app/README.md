# Quickbuddy Pilot App

Pilot client for the shared Quickbuddy API. Connected flows include email/password authentication, limited city-based pilot profile setup, server-authoritative availability, foreground location reporting, live assignment polling, accept/reject, pickup confirmation, adaptive foreground location requests, source-attributed route ETA when available, authorized-zone demand advisories, pilot shift context, external map launch, and pilot earnings ledger reads.

## Local setup

The repository currently has no Flutter/Dart SDK or generated platform runners. Install Flutter with Dart `>=3.9`, then from the repository root run:

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
