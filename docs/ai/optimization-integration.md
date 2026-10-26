# AI and dispatch optimization

Current dispatch recommendations use the established deterministic one-to-one greedy strategy after retrieving eligible tasks and fresh, verified, consented pilots with capacity. Recommendations are not assignments. Task and candidate limits bound work; the output records policy version, runtime, checks and degraded route constraints.

PostGIS routing, merchant-ready sequencing, vehicle-category compatibility, time windows, max detour, freshness and multi-stop batching are not all enforced by the advisory optimizer. It must not be promoted into assignment without those domain checks and transactional validation. LLM output is never used to select or commit a pilot.
