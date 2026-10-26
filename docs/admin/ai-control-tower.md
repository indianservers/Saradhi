# AI control tower

The Company Admin view reads registered model/version metadata from `GET /api/v1/ai/models`, including status and validation flag. It labels this as registry data only and does not infer forecast accuracy, model drift, live demand, latency, or failure risk.

The existing copilot API reports `unavailable` with `no_llm_provider_configured`; the UI does not claim an assistant is active. Model evaluation, forecast provenance dashboards, feature-pipeline status, and recommendation outcomes require read/report contracts not exposed to this workspace.
