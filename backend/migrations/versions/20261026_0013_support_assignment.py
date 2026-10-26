"""Add an auditable owner field for support ticket claims."""

from alembic import op

revision = "20261026_0013"
down_revision = "20261026_0012"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """ALTER TABLE operations.support_tickets
        ADD COLUMN assigned_to_id uuid REFERENCES identity.users(id) ON DELETE RESTRICT"""
    )
    op.execute("""CREATE INDEX ix_support_tickets_assigned_to_id
        ON operations.support_tickets (assigned_to_id)""")


def downgrade():
    raise RuntimeError(
        "Support ownership is operational history; use a reviewed forward repair migration"
    )
