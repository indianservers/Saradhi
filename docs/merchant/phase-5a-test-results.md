# Phase 5.A test results

## Verified in this increment

- `ruff check backend tests`: passed.
- `python -m compileall -q backend tests`: passed.
- Local adapter-contract smoke checks use fixtures for protocol shape and duplicate print-result shape; they do not validate a live POS provider or printer.
- Full repository suite: 75 passed, 1 upstream Starlette/httpx deprecation warning, in 78.28 seconds.
- Real PostgreSQL KDS integration verifies generated prep/packing tasks, deterministic provenance, blocked packing, one-slot station capacity, station assignment, and ready only after all required tasks complete. Merchant pickup and pilot pickup regression scenarios also pass.
- Real PostgreSQL FEFO integration verifies the new branch batch-list response sorts expiring lots and the existing reservation policy still selects eligible stock.
- The integration database is at migration head `20261026_0011`; the integration assertion was updated accordingly. The legacy-order backfill statements were added to the migration source after that local database had already reached this revision, so a fresh-database replay of those specific statements remains a rollout verification step.

## Not verified

No full 50-scenario Phase 5.A suite, bounded load benchmark, p95/p99 latency or lock-contention measurement, 30-concurrent-order test, Flutter build, tablet/phone screenshot comparison, actual POS connector, printer hardware, procurement, recipes, transfers, or bulk import exists in this increment. Flutter/Dart tooling is unavailable in the current environment. These are not inferred from passing backend tests.
