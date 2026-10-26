# Dispatch optimization

`POST /api/v1/ai/dispatch/recommend` and `/optimize` validate the requested unassigned tasks against city, merchant readiness and fulfillment mode. Candidate pilots must be verified, available, consented, have fresh persisted GPS, and have remaining capacity. The bounded greedy plan ranks pickup proximity and workload using the current city policy and recommends at most one task per pilot. It records plan, objective, policy version, constraints and runtime in `intelligence.ai_optimization_decisions`.

The endpoint is advisory (`committed: false`). Assignment is still performed by the transactional Phase 2.B operation after revalidation. The environment lacks PostGIS and route data, so zone serviceability, vehicle/handling compatibility, route time windows and lateness are explicitly marked not evaluated. This is a safe fallback, not the full hybrid optimizer or an OR-Tools solution.
