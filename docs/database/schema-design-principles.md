# Implemented schema principles

Phase 2 schema is now installed; the initial Phase 1 empty-schema gate is historical.
See enterprise-schema.md, data-dictionary.md, schema.json and the actual migration/catalog report.

backend/migrations remains the sole executable Alembic source. database/migrations is reference
only; database/design may contain commented review SQL but never a second runtime history.
No metadata.create_all, startup migrations, reset-by-default scripts or destructive downgrade.

Use real FKs and reviewed constraints, scoped organization/city/branch policies, opaque UUIDv4
identifiers on Python 3.12, UTC timestamptz, explicit IANA schedules and Numeric/Decimal money.
Keep legal-entity/currency books separate and historical financial/item/event records immutable.
Cross-context application services coordinate transactions; domain rules stay framework/ORM free.

Named indexes, per-request sessions, expected versions, row locks, idempotency keys and outbox/
inbox uniqueness enforce critical behavior. Optional PostGIS requires an approved compatible
installation and a reviewed additive spatial migration; no guessed polygon behavior.

Production migration gates: separate runtime/migration roles, verified TLS, current backup and
restore drill, representative upgrade/plan tests, lock budget and forward repair. Preserve PII
retention and residency; do not partition without measured retention/query/uniqueness evidence.
