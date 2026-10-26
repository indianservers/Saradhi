# Live city control tower

Authorized city options are returned by `/api/v1/operations/authorized-cities`. The selected city's dispatch and verified fleet snapshots enforce `dispatch.write` scope in the backend. The city screen exposes active task IDs/status/version only; it does not return customer or pilot PII.

The UI refreshes REST snapshots every 30 seconds. Local capability health currently reports Redis and cross-instance realtime unavailable, so the dashboard does not claim a WebSocket stream or GPS map. Live location persistence exists for the pilot workflows but an authorized multi-pilot map endpoint is not present.
