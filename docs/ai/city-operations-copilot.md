# City operations copilot

`POST /api/v1/ai/agents/city/query` requires an active city and current `ai.read` permission scoped to that city. It summarizes live delivery-state counts and the existing deterministic demand forecast with generation time, source cutoff and provenance. Zone-level pilot supply is not inferred where the system lacks persisted presence.

The response is advisory and read-only. No dispatch policy, pilot assignment or incident is changed. A contextual map panel and alert acknowledgment/escalation flow are not implemented in this phase slice.
