# Connectivity and recovery

Offer and assignment screens reload server state on pull-to-refresh and poll offers every eight seconds while that screen is visible. Accept/reject/pickup actions refresh the assignment after the response and never change local task state optimistically. A lost response is resolved by reloading the authoritative list. Expired offers are rejected by the backend.

The app does not queue online/offline, accept, pickup, or failure commands while disconnected. GPS errors are surfaced on the dashboard; no offline GPS buffer is replayed. Push notifications, WebSocket reconnect, app-killed lifecycle recovery, route-change reconciliation, maps timeout handling, and durable pending-action storage remain unimplemented. On restart the app restores the authenticated session and reloads profile/assignment state.
