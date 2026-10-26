# Pilot copilot

`POST /api/v1/ai/agents/pilot/query` resolves the pilot profile from the current user and returns only active assignments, delivery IDs, statuses and pickup merchant names. It exposes no customer address, phone or arbitrary route proposal. It cannot reorder or alter an assignment.

The delivery app UI, navigation-safe voice interaction, earnings evidence and route-change explanation are not included yet. Existing dispatch and navigation state remain authoritative.
