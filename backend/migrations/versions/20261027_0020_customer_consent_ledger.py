"""Append-only customer-owned marketing consent evidence."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261027_0020"
down_revision = "20261027_0019"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_consent_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(80), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["identity.users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("idempotency_key", name="uq_customer_consent_events_idempotency_key"),
        sa.CheckConstraint(
            "purpose IN ('marketing') AND channel IN ('push','email','sms','whatsapp')",
            name="ck_customer_consent_events_consent_scope",
        ),
        schema="engagement",
    )
    op.create_index(
        "ix_customer_consent_latest",
        "customer_consent_events",
        ["user_id", "purpose", "channel", "created_at"],
        schema="engagement",
    )
    op.create_index(
        "ix_customer_consent_events_user_id",
        "customer_consent_events",
        ["user_id"],
        schema="engagement",
    )
    op.execute(
        "CREATE TRIGGER immutable_record BEFORE UPDATE OR DELETE ON "
        "engagement.customer_consent_events FOR EACH ROW "
        "EXECUTE FUNCTION audit.deny_record_mutation()"
    )


def downgrade():
    raise RuntimeError(
        "Consent evidence is legally significant and cannot be dropped automatically"
    )
