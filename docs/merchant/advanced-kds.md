# Advanced KDS: delivered slice and operator contract

The merchant app now polls an authorized branch's kitchen task list and active stations every 10 seconds. It shows item label/quantity, order reference, station, task state, estimate provenance, target time, dependency blockers, and a disconnected/stale indicator. Pull-to-refresh reloads the authoritative backend queue. Pending work can be assigned to a compatible station. Tasks can be started, paused, resumed, and completed through versioned API transitions. Existing accepted/preparing orders receive pending task rows during migration with `migration_backfill` provenance and no fabricated target timestamp.

The backend creates one prep task per order line and one final packing task when the merchant accepts the order. Default stations are created idempotently (`Main Kitchen`, capacity 8; `Packaging`, capacity 4). Authorized merchants can add stations with a type and capacity. Task routing defaults to Main Kitchen/Packaging; the catalog has no station-routing configuration yet.

The packing task depends on all prep tasks. An order cannot become ready while any task is missing or unfinished. A target completion timestamp is an estimate only and never advances state. Polling is not push real-time; multi-device clients share server state and use optimistic versions.

## API

- `GET /api/v1/merchant/branches/{branch_id}/kitchen/stations`
- `POST /api/v1/merchant/branches/{branch_id}/kitchen/stations`
- `GET /api/v1/merchant/branches/{branch_id}/kitchen/tasks?station_id=&status=&cursor=&limit=`
- `PUT /api/v1/merchant/kitchen/tasks/{task_id}/station`
- `POST /api/v1/merchant/kitchen/tasks/{task_id}/transition`
- Existing `POST /api/v1/merchant-orders/{child_id}/transition` gates `target=ready`.

See [kitchen-state-machine.md](kitchen-state-machine.md) for state and concurrency rules. Recipes, customizations, allergen notes, fullscreen/tablet layout, sound alerts, and station-specific product routing are not represented in this API yet.
