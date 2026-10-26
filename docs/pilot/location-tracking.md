# Pilot location tracking

The app uses Geolocator foreground location only. Before tracking, it explains the purpose and posts `POST /api/v1/pilots/me/location-consent`. It requests device permission, rejects local samples with accuracy worse than 100 metres, then sends an immediate location and subsequent distance-filtered updates while online. Sequence numbers persist in secure storage. API timestamps are UTC/offset-aware; the server rejects stale, out-of-order, inaccurate, or implausible jumps.

Going online is accepted only after a fresh location and consent are present. Local online UI is refreshed from `GET /api/v1/pilots/me` after the server transition succeeds. A failed online request stops the local GPS stream. Going offline calls the backend first; an active assignment rejection leaves tracking active. Sign-out stops the location stream. Offline pilots are not tracked.

No background location permission/service is requested. The stream is foreground-only and does not promise exact intervals or OS continuity. Platform runners must be generated with `tools/dev.ps1 flutter-init -App pilot_app`; that initializer adds Android coarse/fine foreground permissions and iOS `WhenInUse` disclosure. No `Always`/background permission is added. Physical battery and lifecycle behavior are not measured in this environment.
