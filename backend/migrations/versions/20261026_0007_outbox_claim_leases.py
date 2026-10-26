"""Add short-lived durable claims so broker I/O happens outside row-lock transactions."""

from alembic import op

revision = "20261026_0007"
down_revision = "20261026_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE integration.outbox_events
        ADD COLUMN claim_token uuid,
        ADD COLUMN claim_expires_at timestamptz""")
    op.execute("""ALTER TABLE integration.outbox_events
        ADD CONSTRAINT ck_outbox_claim_pair CHECK (
          (claim_token IS NULL) = (claim_expires_at IS NULL)
        )""")
    op.execute("""CREATE INDEX ix_outbox_claimable
        ON integration.outbox_events (available_at, claim_expires_at, id)
        WHERE delivered_at IS NULL AND dead_lettered_at IS NULL""")


def downgrade():
    raise RuntimeError("Outbox lease history is forward-only; use a reviewed repair migration")
