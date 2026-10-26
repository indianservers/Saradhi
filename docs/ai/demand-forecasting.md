# Demand forecasting

`GET /api/v1/ai/demand/cities/{city_id}/forecast` and `/zones/{zone_id}/forecast` return 30-minute, 1-hour, 4-hour and 24-hour estimates. The deterministic seasonal baseline averages same weekday/hour observations over the preceding 28 days. Unobserved hours are zero; a zone with no mapped order history is marked `cold_start_fallback`. The endpoint returns feature version, source cutoff, sample count and provenance and persists the forecast.

This is an untrained baseline, not a learned production model. `POST /api/v1/ai/models/{model_id}/evaluate` is restricted to `ai.manage` and performs a chronological expanding-window backtest only when actual history exists. It reports MAE, RMSE, WAPE and bias; WAPE is undefined for zero total demand. No accuracy claim is made for cold-start cities.

Example:

```powershell
curl.exe -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/ai/demand/cities/<city-id>/forecast
```

## Local data readiness

The development database currently has 0 orders, so there is no real local history for forecast accuracy evaluation. The test database contains integration fixtures (1,704 orders); those records are explicitly excluded from training. Preparation-duration labels are also 0 because the event schema has no per-merchant-order start/ready timestamp pair. See [data-readiness.json](data-readiness.json) for the generated counts. Forecast behavior is validated with synthetic/unit and API fixtures only.

