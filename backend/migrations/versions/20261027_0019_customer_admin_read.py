"""Grant the new customer admin read permission to audited admin roles."""

from uuid import UUID, uuid5

from alembic import op

revision = "20261027_0019"
down_revision = "20261027_0018"
branch_labels = None
depends_on = None

NAMESPACE = UUID("14e57ad0-467c-4f88-a4e8-515a6c2a6b54")


def identifier(name):
    return str(uuid5(NAMESPACE, name))


def upgrade():
    permission_id = identifier("permission:customer.read")
    op.execute(
        "INSERT INTO identity.permissions(id,code) "
        f"VALUES ('{permission_id}','customer.read') ON CONFLICT (code) DO NOTHING"
    )
    for role in ("platform_super_admin", "company_admin", "city_manager"):
        op.execute(
            "INSERT INTO identity.role_permissions(id,role_id,permission_id) "
            f"VALUES ('{identifier(role + ':customer.read')}',"
            f"'{identifier('role:' + role)}','{permission_id}') "
            "ON CONFLICT DO NOTHING"
        )


def downgrade():
    raise RuntimeError("Removing CRM read grants may revoke production access; review explicitly")
