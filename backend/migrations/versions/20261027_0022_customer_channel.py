"""Customer-facing merchant metadata and preparation notes."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20261027_0022"
down_revision = "20261027_0021"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "cart_items",
        sa.Column("preparation_notes", sa.Text(), nullable=False, server_default=""),
        schema="commerce",
    )
    op.create_table(
        "product_customer_details",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("catalog.products.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ingredients", JSONB(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("allergens_reviewed", sa.Boolean(), server_default="false", nullable=False),
        sa.UniqueConstraint("product_id"),
        schema="catalog",
    )


def downgrade():
    op.drop_table("product_customer_details", schema="catalog")
    op.drop_column("cart_items", "preparation_notes", schema="commerce")
