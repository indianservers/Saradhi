"""Give kitchen workflows a dedicated, branch-scoped permission."""

from uuid import UUID, uuid5

from alembic import op

revision = "20261027_0021"
down_revision = "20261027_0020"
branch_labels = None
depends_on = None

NAMESPACE = UUID("14e57ad0-467c-4f88-a4e8-515a6c2a6b54")


def identifier(name):
    return str(uuid5(NAMESPACE, name))


def upgrade():
    permission_id = identifier("permission:kitchen.manage")
    op.execute(
        f"INSERT INTO identity.permissions(id,code) VALUES ('{permission_id}','kitchen.manage') "
        "ON CONFLICT (code) DO NOTHING"
    )
    # Kitchen operators must not inherit general merchant administration or inventory access.
    op.execute(
        "DELETE FROM identity.role_permissions rp USING identity.roles r, identity.permissions p "
        "WHERE rp.role_id=r.id AND rp.permission_id=p.id "
        "AND r.name='kitchen_operator' AND p.code IN ('merchant.write','inventory.read')"
    )
    for role in ("platform_super_admin", "merchant_owner", "branch_manager", "kitchen_operator"):
        op.execute(
            "INSERT INTO identity.role_permissions(id,role_id,permission_id) "
            f"VALUES ('{identifier(role + ':kitchen.manage')}',"
            f"'{identifier('role:' + role)}','{permission_id}') ON CONFLICT DO NOTHING"
        )


def downgrade():
    raise RuntimeError("Restoring broad kitchen permissions requires a reviewed security migration")
