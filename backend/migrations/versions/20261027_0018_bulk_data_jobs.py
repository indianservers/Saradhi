"""Create scoped branch import job records and stable source references."""

from uuid import UUID, uuid5

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261027_0018"
down_revision = "20261027_0017"
branch_labels = None
depends_on = None

NAMESPACE = UUID("14e57ad0-467c-4f88-a4e8-515a6c2a6b54")


def identifier(value):
    return str(uuid5(NAMESPACE, value))


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS admin")
    op.create_table(
        "bulk_data_jobs",
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), server_default="VALIDATED", nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("row_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("previewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mapping", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('VALIDATED','PROCESSING','COMPLETED',"
            "'PARTIALLY_COMPLETED','FAILED','CANCELLED')",
            name="ck_bulk_data_jobs_bulk_job_status",
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["identity.users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "actor_id", "idempotency_key", name="uq_bulk_data_jobs_actor_idempotency_key"
        ),
        schema="admin",
    )
    op.create_index("ix_bulk_data_jobs_actor_id", "bulk_data_jobs", ["actor_id"], schema="admin")
    op.create_table(
        "bulk_data_job_rows",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("errors", postgresql.JSONB(), server_default="[]", nullable=False),
        sa.Column("status", sa.Text(), server_default="valid", nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["admin.bulk_data_jobs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "row_number", name="uq_bulk_data_job_rows_job_row"),
        schema="admin",
    )
    op.create_index(
        "ix_bulk_data_job_rows_job_id", "bulk_data_job_rows", ["job_id"], schema="admin"
    )
    op.create_table(
        "bulk_external_refs",
        sa.Column("entity", sa.Text(), nullable=False),
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity", "source_key", name="uq_bulk_external_refs_entity_source_key"),
        schema="admin",
    )
    permission_id = identifier("permission:merchant.export")
    op.execute(
        f"INSERT INTO identity.permissions(id,code) VALUES ('{permission_id}','merchant.export')"
    )
    for role in ("platform_super_admin", "company_admin", "city_manager"):
        role_id = identifier("role:" + role)
        link_id = identifier(role + ":merchant.export")
        op.execute(
            "INSERT INTO identity.role_permissions(id,role_id,permission_id) "
            f"VALUES ('{link_id}','{role_id}','{permission_id}')"
        )


def downgrade():
    raise RuntimeError("Bulk job audit data is operational history; use a reviewed forward repair")
