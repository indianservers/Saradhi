# Merchant inventory management

The app reads branch stock balances from the shared inventory API, displaying on-hand, reserved and sellable quantity. It does not infer recipe ingredients or BOM usage. Stock adjustment posts a signed delta and a fresh idempotency key; backend branch authorization, stock row locking, reserved-floor validation, batch policy and actor-attributed stock movement remain authoritative.

Current rows show variant IDs because the inventory endpoint does not join catalogue labels; product/variant names are available in the branch catalogue screen. The app does not invent low-stock thresholds. Stock movement history, receiving/batch/expiry UI, reason codes, per-SKU search/filter, low-stock configuration and restaurant menu availability controls are follow-up work. Backend transactions and concurrency behavior have existing tests, but no physical merchant-device test ran in this phase.
