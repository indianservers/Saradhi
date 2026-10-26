"""Link the shared operational incidents ledger to pilot/task safety reports."""

from alembic import op

revision = "20261026_0012"
down_revision = "20261026_0011"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE operations.operational_incidents
        ADD COLUMN pilot_id uuid REFERENCES fulfillment.pilot_profiles(id) ON DELETE RESTRICT,
        ADD COLUMN delivery_task_id uuid REFERENCES fulfillment.delivery_tasks(id)
            ON DELETE RESTRICT,
        ADD COLUMN reporter_id uuid REFERENCES identity.users(id) ON DELETE RESTRICT,
        ADD COLUMN category text,
        ADD COLUMN resolution_summary text,
        ADD COLUMN safety_emergency boolean NOT NULL DEFAULT false""")
    op.execute("""CREATE INDEX ix_pilot_incidents_city_status_created
        ON operations.operational_incidents (city_id, status, created_at DESC)
        WHERE reporter_id IS NOT NULL""")
    op.execute("""CREATE INDEX ix_pilot_incidents_pilot_created
        ON operations.operational_incidents (pilot_id, created_at DESC)
        WHERE pilot_id IS NOT NULL""")


def downgrade():
    raise RuntimeError(
        "Pilot incident records are forward-only; use a reviewed repair migration"
    )
