# Phase 2.C status

Delivered: point-in-time city/zone demand features and a seasonal deterministic forecast; chronological backtest metrics; transparent preparation estimate; Phase 2.B ETA integration with explicit provider fallback; bounded advisory dispatch recommendations; availability-filtered merchant/product recommendations; review-only delay risk signals; persisted inference/evaluation/forecast/optimization metadata; scoped API surfaces; and explicit unavailable status for the LLM copilot.

No ML model was trained. Historical labels are inadequate for honest training or accuracy claims. NumPy/Pandas/scikit-learn/OR-Tools/MLflow are not installed. PostGIS, Redis and a road-routing provider remain unavailable in the local environment. Multi-stop batching, zone-level positioning, trained cancellation/fraud/ETA models, canary promotion/rollback workflows, scheduled training, and a permissioned LLM tool gateway are not production-complete. Deterministic inference remains optional and does not block order/delivery transactions.

Run migrations and tests:

```powershell
.venv\Scripts\python.exe -m backend.scripts.migrate
.venv\Scripts\python.exe -m pytest tests/unit tests/integration tests/contract -q
```

Before Phase 3, provision durable Redis/PostGIS/maps services, record reliable preparation and delivery outcome timestamps, build governed point-in-time datasets, add role-scoped operational approval workflows, and benchmark forecasting/dispatch against time-based holdouts and production-like load. Keep rule-based inference in shadow/advisory mode until these evaluations pass.

## Local evidence

The development database has no order history (0 orders); the test database's 1,704 orders are integration fixtures and excluded from training. Preparation-duration labels are 0 because start/ready timestamps are not recorded per merchant order. Generated non-PII counts are in [data-readiness.json](data-readiness.json). Consequently, the delivered demand baseline has no real-data accuracy result.

