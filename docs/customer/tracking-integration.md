# Tracking integration

The app requests `GET /api/v1/orders/{order_id}/tracking`, which checks that the authenticated user owns the parent order. It refreshes the snapshot every 15 seconds and offers manual retry after an error. Delivery status and pilot coordinates are rendered only when returned by the backend; absent/stale pilot location is shown as unavailable. The current UI does not render an ETA.

The API exposes realtime tickets and an authorized WebSocket, but the Flutter app does not yet connect to the WebSocket. No map tile provider/key is configured, so there is no map view or interpolated marker. Polling may show delayed updates and should not be represented as sub-second live tracking. A later poll failure retains the last good snapshot with an explicit last-known label.
