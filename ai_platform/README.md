# Quickbuddy AI platform

Phase 2.C adds deterministic, CPU-only inference and optimization under this package. See `docs/ai/` for feature provenance, API behavior, model status, lifecycle boundaries and production blockers.

Run baseline unit and database-backed API tests:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_ai_baselines.py tests/integration -q
```

No model is trained or advertised as trained. Train only after governed, point-in-time labels and a reviewed evaluation split exist. The `intelligence` schema keeps forecasts, inference runs, evaluations and optimization recommendations separate from order/finance records.
