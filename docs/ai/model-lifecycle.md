# Model lifecycle and operations

Migration `20261026_0010` extends the existing version registry with algorithm, code/feature schema versions, dataset reference, metrics, artifact checksum, validation and lifecycle status. It adds training-job, feature-pipeline-run, forecast-output and optimization-decision records. Deterministic baseline model/version records are seeded as `status=deterministic`; they have no trained artifact, dataset or accuracy metrics.

`GET /api/v1/ai/models` and `/models/{model_id}/metrics` expose registry metadata. The demand evaluator is `POST /models/{model_id}/evaluate`, restricted to platform `ai.manage`; it stores a time-split evaluation only for observed history. There is no training command because no suitable historical labels are available. Do not promote a model from this baseline registry without real data, validation, approval, artifact checksum and rollback evidence.

Local workflow:

```powershell
.venv\Scripts\python.exe -m backend.scripts.migrate
.venv\Scripts\python.exe -m pytest tests/unit tests/integration -q
```
