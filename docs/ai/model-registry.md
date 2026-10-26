# Model registry and lifecycle

The existing intelligence registry stores deterministic baseline model/version metadata, evaluation runs, feature schema versions, artifact checksum fields and training-job records. The API lists models and evaluates the demand baseline using a time-ordered holdout. Seeded rows are marked `deterministic`, not trained.

No training runner, dataset governance pipeline, artifact store, checksum validation, shadow/canary promotion, production approval, rollback API, retirement workflow or MLflow service is deployed. Retraining must wait for sufficient legitimate point-in-time labels and a reproducible holdout.
