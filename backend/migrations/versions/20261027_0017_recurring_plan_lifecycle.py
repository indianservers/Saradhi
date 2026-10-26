"""Persist explicit recurring-plan lifecycle state."""

from alembic import op

revision = "20261027_0017"
down_revision = "20261026_0016"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE fulfillment.recurring_order_plans "
        "ADD COLUMN status text NOT NULL DEFAULT 'active'"
    )
    op.execute("UPDATE fulfillment.recurring_order_plans SET status='paused' WHERE active IS FALSE")
    op.execute(
        "ALTER TABLE fulfillment.recurring_order_plans "
        "ADD CONSTRAINT ck_recurring_order_plans_rule_0 "
        "CHECK (status IN ('active','paused','cancelled'))"
    )


def downgrade():
    op.execute(
        "ALTER TABLE fulfillment.recurring_order_plans "
        "DROP CONSTRAINT ck_recurring_order_plans_rule_0"
    )
    op.execute("ALTER TABLE fulfillment.recurring_order_plans DROP COLUMN status")
