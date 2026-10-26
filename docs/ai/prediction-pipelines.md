# Prediction pipelines

The existing pipeline uses point-in-time hourly order aggregates, a same-weekday/hour seasonal-naive forecast, chronological rolling backtests and explicit cold-start zero output. ETA delegates to the Phase 2.B route provider; preparation uses a transparent item/queue rule. Every output reports baseline provenance/version. No trained predictor is deployed.

The last captured readiness report had no development orders, no ETA outcome samples and no preparation labels; test fixtures are excluded. No accuracy score is asserted. Forecast by category/window, preparation labels, trained ETA, interval calibration, city/zone fairness metrics and scheduled evaluation require data and lifecycle work.
