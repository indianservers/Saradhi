# Constraint verification

Catalog and model audit was run on PostgreSQL 17.11 at migration `20261026_0007` for both
configured local databases. Registered ORM tables and columns match exactly (247 tables,
1,661 columns each). There are 796 PostgreSQL constraints per database, including the
migration-managed `ck_outbox_claim_pair`; that check is validated. The outbox-specific check is
reported separately because Alembic operational constraints are intentionally outside ORM
metadata. The catalog audit found zero invalid indexes and zero unvalidated constraints.

Constraint families include primary and unique keys, foreign keys, nonnegative/positive and
bounded inventory/amount checks, finite coordinate and latitude/longitude ranges, assignment
exclusivity, version/idempotency uniqueness, and deferred financial journal balance guards.
Financial integration tests exercise balanced posts, rejection of cross-currency imbalance,
deferred database rejection of unbalanced journal writes that bypass service validation,
immutability of posted journal data, idempotent reversals, and sandbox refund caps/approval.

`RESTRICT` foreign keys are deliberate. The installed FK/unique/check constraints protect
referential and transaction invariants at the database layer. We did not run a bulk orphan scan
on the development database or mutate it with fixtures. Detailed catalogs:
`../operations/phase-2-database-evidence.json`; model/catalog column audit:
`../operations/phase-2a-schema-evidence.json`.
