# AI and operational estimates

The task target time is currently produced by `preparation_rule` in `ai_platform.inference.service`. Each task stores `estimate_provenance=deterministic_rule` and the returned model version (currently `preparation-v1`). The estimate is a cold-start/deterministic rule, not a trained restaurant prediction. Its timestamp does not automatically complete work or change customer commitments.

No merchant-specific sales/product performance, shortage/reorder, cancellation, delay, staffing, or capacity recommendations were added. Do not present the estimate as a trained prediction or claim uncertainty intervals not returned by the service. No recommendation automatically changes availability, prices, procurement, or schedules.
