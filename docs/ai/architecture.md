# Quickbuddy AI platform

The first AI release uses Python modules under `ai_platform/` and the existing PostgreSQL `intelligence` schema. Inference is invoked from FastAPI requests with bounded queries; it does not train models or call external services. Forecast and decision outputs are persisted separately from checkout, and order processing has no dependency on AI availability.

The platform registry identifies built-in deterministic baselines as `deterministic`, not trained. `GET /api/v1/ai/models` exposes status and provenance. The local environment has no NumPy, Pandas, scikit-learn, OR-Tools, MLflow, TensorFlow or PyTorch installed, so this phase deliberately uses the standard library and existing SQLAlchemy/PostgreSQL dependencies.

Quick check:

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_ai_baselines.py tests/integration/test_reliability.py -q
```

No GPU or external AI provider is required. The copilot reports unavailable until a provider and reviewed tool policies are configured.
