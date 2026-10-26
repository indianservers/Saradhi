"""Add point-in-time AI pipeline, forecast, optimization and lifecycle metadata."""

from uuid import UUID, uuid5

from alembic import op
from sqlalchemy import text

revision = "20261026_0010"
down_revision = "20261026_0009"
branch_labels = None
depends_on = None

NAMESPACE = UUID("14e57ad0-467c-4f88-a4e8-515a6c2a6b54")


def ident(value):
    return str(uuid5(NAMESPACE, value))


def execute(statement, params=None):
    op.get_bind().execute(text(statement), params or {})


def upgrade():
    op.execute("""ALTER TABLE intelligence.ai_model_versions
        ADD COLUMN algorithm text NOT NULL DEFAULT 'untrained',
        ADD COLUMN training_code_version text NOT NULL DEFAULT 'unknown',
        ADD COLUMN dataset_reference text,
        ADD COLUMN feature_schema_version text NOT NULL DEFAULT 'v1',
        ADD COLUMN trained_at timestamptz,
        ADD COLUMN metrics jsonb NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN artifact_checksum text,
        ADD COLUMN validation_passed boolean NOT NULL DEFAULT false,
        ADD COLUMN status text NOT NULL DEFAULT 'untrained'""")
    op.execute("""CREATE TABLE intelligence.ai_training_jobs (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        model_id uuid NOT NULL REFERENCES intelligence.ai_model_registry(id) ON DELETE RESTRICT,
        status text NOT NULL,
        dataset_reference text NOT NULL,
        sample_count integer NOT NULL,
        code_version text NOT NULL,
        feature_schema_version text NOT NULL,
        metrics jsonb NOT NULL,
        started_at timestamptz,
        finished_at timestamptz,
        error_code text,
        CONSTRAINT ck_ai_training_jobs_rule_0 CHECK (sample_count >= 0),
        CONSTRAINT ck_ai_training_jobs_rule_1 CHECK
          (status IN ('queued','running','succeeded','failed','cancelled')),
        CONSTRAINT ck_ai_training_jobs_rule_2 CHECK ((started_at IS NULL) = (status = 'queued'))
    )""")
    op.execute(
        "CREATE INDEX ix_ai_training_jobs_model_id ON intelligence.ai_training_jobs(model_id)"
    )
    op.execute("""CREATE TABLE intelligence.ai_feature_pipeline_runs (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        feature_schema_version text NOT NULL,
        source_cutoff timestamptz NOT NULL,
        row_count integer NOT NULL,
        quality jsonb NOT NULL,
        status text NOT NULL,
        CONSTRAINT ck_ai_feature_pipeline_runs_rule_0 CHECK (row_count >= 0),
        CONSTRAINT ck_ai_feature_pipeline_runs_rule_1 CHECK
          (status IN ('succeeded','failed','partial'))
    )""")
    op.execute("""CREATE TABLE intelligence.ai_forecast_outputs (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        city_id uuid NOT NULL REFERENCES geo.cities(id) ON DELETE RESTRICT,
        zone_id uuid REFERENCES geo.service_zones(id) ON DELETE RESTRICT,
        interval_minutes integer NOT NULL,
        forecast jsonb NOT NULL,
        provenance text NOT NULL,
        feature_schema_version text NOT NULL,
        source_cutoff timestamptz NOT NULL,
        expires_at timestamptz NOT NULL,
        CONSTRAINT ck_ai_forecast_outputs_rule_0 CHECK (interval_minutes > 0)
    )""")
    op.execute(
        "CREATE INDEX ix_ai_forecast_outputs_city_id ON intelligence.ai_forecast_outputs(city_id)"
    )
    op.execute(
        "CREATE INDEX ix_ai_forecast_outputs_zone_id ON intelligence.ai_forecast_outputs(zone_id)"
    )
    op.execute("""CREATE TABLE intelligence.ai_optimization_decisions (
        id uuid PRIMARY KEY,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now(),
        city_id uuid NOT NULL REFERENCES geo.cities(id) ON DELETE RESTRICT,
        mode text NOT NULL,
        policy_version text NOT NULL,
        objective_score numeric(20,4) NOT NULL,
        plan jsonb NOT NULL,
        constraint_checks jsonb NOT NULL,
        runtime_ms integer NOT NULL,
        fallback_reason text,
        CONSTRAINT ck_ai_optimization_decisions_rule_0 CHECK (runtime_ms >= 0)
    )""")
    op.execute(
        "CREATE INDEX ix_ai_optimization_decisions_city_id "
        "ON intelligence.ai_optimization_decisions(city_id)"
    )
    execute(
        "INSERT INTO identity.permissions (id, code) VALUES "
        "(:read_id, 'ai.read'), (:manage_id, 'ai.manage')",
        {"read_id": ident("permission:ai.read"), "manage_id": ident("permission:ai.manage")},
    )
    for role in (
        "platform_super_admin",
        "company_admin",
        "country_manager",
        "city_manager",
        "city_operator",
        "zone_manager",
        "merchant_owner",
        "branch_manager",
    ):
        execute(
            """INSERT INTO identity.role_permissions (id, role_id, permission_id)
            SELECT :assignment_id, r.id, p.id FROM identity.roles r, identity.permissions p
            WHERE r.name=:role AND p.code='ai.read'""",
            {"assignment_id": ident(role + ":ai.read"), "role": role},
        )
    execute(
        """INSERT INTO identity.role_permissions (id, role_id, permission_id)
        SELECT :assignment_id, r.id, p.id FROM identity.roles r, identity.permissions p
        WHERE r.name='platform_super_admin' AND p.code='ai.manage'""",
        {"assignment_id": ident("platform_super_admin:ai.manage")},
    )
    baselines = (
        ("demand", "Seasonal naive city demand forecast", "seasonal_naive_v1"),
        ("preparation", "Transparent preparation duration rule", "queue_item_rule_v1"),
        ("eta", "Road provider ETA baseline", "road_duration_rule_v1"),
        ("dispatch", "Deterministic dispatch scoring", "weighted_score_v1"),
        ("risk", "Review-only operational risk signals", "operational_rules_v1"),
        ("recommendations", "Availability-filtered popularity ranking", "popularity_v1"),
    )
    for key, purpose, algorithm in baselines:
        model_id = ident("ai-baseline:" + key)
        version_id = ident("ai-baseline-version:" + key + ":v1")
        execute(
            """INSERT INTO intelligence.ai_model_registry (id,name,purpose,provider)
            VALUES (:model_id,:name,:purpose,'builtin') ON CONFLICT (id) DO NOTHING""",
            {"model_id": model_id, "name": f"quickbuddy-{key}-baseline", "purpose": purpose},
        )
        execute(
            """INSERT INTO intelligence.ai_model_versions
            (id,model_id,version,artifact_reference,algorithm,training_code_version,
             feature_schema_version,metrics,validation_passed,status)
            VALUES (:version_id,:model_id,'v1',:artifact_reference,:algorithm,'phase-2c-v1',
             'quickbuddy-operational-v1','{}'::jsonb,false,'deterministic')
            ON CONFLICT (id) DO NOTHING""",
            {
                "version_id": version_id,
                "model_id": model_id,
                "artifact_reference": f"builtin://quickbuddy/ai/{key}/v1",
                "algorithm": algorithm,
            },
        )


def downgrade():
    raise RuntimeError(
        "AI evaluation and decision records are retained; use a reviewed forward migration"
    )
