# Feature pipelines

`ai_platform/features/contracts.py` defines the feature schema version and event/availability timestamps. The city demand pipeline reads distinct orders joined to merchant branches, filters source events at or before its cutoff, aggregates by city-local hour, fills unobserved hours with zero, and excludes customer identity, address and payment fields. It records source, transformation, missing-value policy and quality summary in `intelligence.ai_feature_pipeline_runs`.

The demand API uses a 28-day lookback. Zone features are limited to explicit merchant service-area-to-zone mappings; unmapped zones produce an honest zero-history cold start. Input feature values and prediction outputs are digested or retained only as needed. Do not add post-event outcomes to online features without a separate point-in-time audit.

Run against local databases:

```powershell
.venv\Scripts\python.exe -m backend.scripts.migrate
.venv\Scripts\python.exe -m backend.scripts.phase2a_schema_audit
```
