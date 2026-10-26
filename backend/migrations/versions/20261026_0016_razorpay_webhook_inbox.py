"""Persist authenticated Razorpay webhook deliveries, including unmatched references."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261026_0016"
down_revision = "20261026_0015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "razorpay_webhook_events",
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("payload_hash", sa.Text(), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_payment_id", sa.Text(), nullable=True),
        sa.Column("provider_order_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), server_default="received", nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('received','processed','unmatched','ignored','rejected')",
            name="ck_razorpay_webhook_events_razorpay_webhook_status",
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["finance.payment_intents.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_razorpay_webhook_events_event_id"),
        schema="finance",
    )
    op.create_index(
        "ix_razorpay_webhook_events_provider_order_id",
        "razorpay_webhook_events",
        ["provider_order_id"],
        schema="finance",
    )


def downgrade():
    op.drop_index(
        "ix_razorpay_webhook_events_provider_order_id",
        table_name="razorpay_webhook_events",
        schema="finance",
    )
    op.drop_table("razorpay_webhook_events", schema="finance")
