"""Persist FEFO allocation state and batch-specific movement references."""

from pathlib import Path

from alembic import op

revision = "20261026_0004"
down_revision = "20261026_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""ALTER TABLE inventory.stock_batches ADD COLUMN reserved numeric(20,4)
        NOT NULL DEFAULT 0, ADD CONSTRAINT ck_stock_batches_rule_1
        CHECK (reserved BETWEEN 0 AND quantity)""")
    op.execute(
        Path(__file__).with_name("20261026_0004_batch_table.sql").read_text(encoding="utf-8")
    )
    op.execute("""CREATE INDEX ix_batch_reservation_allocations_reservation_id
        ON inventory.batch_reservation_allocations(reservation_id)""")
    op.execute("""CREATE INDEX ix_batch_reservation_allocations_batch_id
        ON inventory.batch_reservation_allocations(batch_id)""")
    op.execute("""ALTER TABLE inventory.stock_movements ADD COLUMN batch_id uuid,
        ADD CONSTRAINT fk_stock_movements_batch_id_stock_batches
        FOREIGN KEY(batch_id) REFERENCES inventory.stock_batches(id) ON DELETE RESTRICT""")


def downgrade():
    raise RuntimeError("Removing inventory traceability requires explicit review")
