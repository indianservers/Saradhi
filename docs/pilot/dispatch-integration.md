# Dispatch and offer integration

`GET /api/v1/pilots/me/assignments` derives pilot identity from the authenticated principal and returns only that pilot's active offered/accepted/picked-up assignments. Offered responses omit the exact recipient address; acceptance reveals the assigned snapshot. The app polls this list while viewing offers and refreshes after actions. It displays server expiration time and does not treat a local countdown as authority.

Accept/reject call the existing versioned, transaction-safe shared dispatch APIs. An assignment is shown as accepted only after a successful response and a fresh authoritative read. Retries after a timeout first reload assignment state. No new dispatch engine, candidate selection, payout calculation, push channel, or WebSocket offer subscription was added. The backend still issues offers through its existing dispatch/operations path.
