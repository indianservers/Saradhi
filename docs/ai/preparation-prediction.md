# Preparation-time prediction

`POST /api/v1/ai/preparation/predict` requires branch-scoped `ai.read`, derives current accepted/preparing queue depth from PostgreSQL, and accepts a bounded item count. The current transparent rule is `12 minutes + 2 minutes per item + 4 minutes per queued order`, capped at 120 minutes. It returns no uncertainty interval and identifies itself as `deterministic_rule` / `untrained_baseline`.

The result is advice only and never updates merchant-reported preparation status. Existing status history does not provide enough reliable preparation start/ready labels to claim a trained estimate. Collect those timestamps before fitting and evaluating a model.
