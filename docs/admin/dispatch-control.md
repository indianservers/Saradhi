# Dispatch control

The live dispatch view uses `GET /api/v1/operations/cities/{city_id}/dispatch` and displays its bounded active-task IDs, states, versions, and authoritative state counts. The backend validates `dispatch.write` for the selected city. City pilot incidents use the corresponding incident read/acknowledge/resolve APIs.

Candidate-pilot inspection, retries, reassignment, routing constraints, reason codes for reassignment, live map layers, WebSocket snapshot recovery, and customer-safe ETA details are not available to these apps because no suitable scoped API contract was found. No task record is directly edited from the UI.
