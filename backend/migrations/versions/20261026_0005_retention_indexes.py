"""Index pilot history and proof retention without partitioning transactional tables."""

from alembic import op

revision = "20261026_0005"
down_revision = "20261026_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_pilot_history_subject_time",
        "pilot_location_events",
        ["pilot_id", "observed_at", "id"],
        schema="fulfillment",
    )
    op.create_index(
        "ix_pilot_history_retention",
        "pilot_location_events",
        ["expires_at", "id"],
        schema="fulfillment",
    )
    op.create_index(
        "ix_delivery_proof_retention",
        "proof_of_delivery",
        ["expires_at", "id"],
        schema="fulfillment",
    )


def downgrade():
    raise RuntimeError("Index removal requires reviewed performance evidence")
