# Recipes and ingredient inventory

## Existing inventory behavior

Quickbuddy has branch stock balances and actor-attributed adjustments. `backend/application/batches.py` allocates eligible batches in FEFO order under row locks, records reservation allocations, and consumes or releases those allocations idempotently with the reservation lifecycle. Batch receipt rejects already-expired sellable stock. This applies to sellable variant stock.

## Not implemented in Phase 5.A

There is no recipe/BOM, ingredient, packaging-material, recipe revision, conversion, yield, wastage, substitution, stock-count, or ingredient-consumption workflow in this increment. KDS completion therefore does not deduct recipe ingredients. Do not treat sellable item FEFO as ingredient inventory. Recipe consumption requires a separate immutable recipe-version snapshot and transactionally idempotent movement design before it is enabled.
