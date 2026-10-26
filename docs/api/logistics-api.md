# Logistics API

The shared versioned API provides pilot location consent and ingestion, pilot availability, order tracking, delivery detail/timeline/ETA, assignment accept/reject, city dispatch/fleet snapshots, dispatch-policy versioning, manual reassignment, pickup and delivery-task failure. Routes are documented in generated `packages/api_contracts/openapi.json`.

Authorization is resource-scoped. Customer tracking is restricted to order owner; merchant/city access uses membership/area scope; pilots see their assignments. WebSocket tickets are single-use and short-lived. ETA returns 503 when a road provider is unavailable. GPS ingestion can persist while Redis is unavailable, but cached presence and live fan-out cannot be claimed operational.
