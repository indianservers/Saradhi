# AI control tower

The Company Admin view reads registered model/version metadata from `GET /api/v1/ai/models`, including status and validation flag. It labels this as registry data only and does not infer forecast accuracy, model drift, live demand, latency, or failure risk. Other AI routes produce forecasts and recommendations with recorded provenance.

The existing copilot API reports unavailable with `no_llm_provider_configured`; the UI does not claim an assistant is active. No AI output is automatically applied to dispatch or finance. Model evaluation, forecast provenance dashboards, feature-pipeline status, recommendation outcomes, model rollback controls, and drift alarms need additional read/control contracts and are not delivered in this slice.
