# Customer tracking QA

Date: 2026-10-26.

## Implemented client behavior

`/orders/:orderId/tracking` requests the owner-authorized tracking snapshot, refreshes every 15 seconds, prevents overlapping polls, cancels its timer on dispose, exposes manual retry and labels the last successful snapshot if a later request fails. The map placeholder explicitly says no rider movement is simulated; unavailable coordinates remain unavailable. The order detail provides a support shortcut.

## Verification and limits

Backend snapshot ownership/security is covered in the API integration suite; all **29 integration tests passed** in the latest run. No Flutter screen, GPS disconnect/reconnect, frame stability or permission flow could be executed because Flutter/Dart tooling is unavailable.

There is no configured Flutter WebSocket consumer, map tile provider, route polyline, marker interpolation, ETA display, or dedicated GPS freshness UI. The screen refreshes snapshots by polling, not by the Phase 2.B realtime event stream. Multi-merchant child deliveries are only shown if returned in the snapshot; individual map/ETA route is incomplete. Tracking authorization expiry behavior has not been device-tested.

Do not describe this as live map tracking or claim reconnecting WebSocket behavior. It is periodic authorized snapshot refresh with last-known-state fallback.
