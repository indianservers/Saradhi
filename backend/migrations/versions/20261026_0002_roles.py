"""Permission master data only. No users, merchants or business transactions."""

from uuid import UUID, uuid5

from alembic import op

revision = "20261026_0002"
down_revision = "20261026_0001"
branch_labels = None
depends_on = None

PERMISSIONS = [
    "geo.write",
    "merchant.write",
    "merchant.approve",
    "catalog.write",
    "inventory.write",
    "inventory.read",
    "dispatch.write",
    "pilot.verify",
    "finance.write",
    "finance.read",
    "finance.configure",
    "support.write",
    "audit.read",
    "organization.members",
]
ROLES = {
    "platform_super_admin": PERMISSIONS,
    "company_admin": [
        "merchant.approve",
        "merchant.write",
        "catalog.write",
        "inventory.read",
        "dispatch.write",
        "audit.read",
        "organization.members",
    ],
    "country_manager": ["merchant.approve", "dispatch.write", "audit.read"],
    "city_manager": ["merchant.approve", "dispatch.write", "audit.read"],
    "city_operator": ["dispatch.write", "inventory.read"],
    "zone_manager": ["dispatch.write"],
    "merchant_owner": [
        "merchant.write",
        "catalog.write",
        "inventory.write",
        "inventory.read",
        "dispatch.write",
        "organization.members",
        "audit.read",
    ],
    "branch_manager": [
        "merchant.write",
        "catalog.write",
        "inventory.write",
        "inventory.read",
        "dispatch.write",
    ],
    "kitchen_operator": ["merchant.write", "inventory.read"],
    "delivery_fleet_manager": ["dispatch.write"],
    "delivery_pilot": [],
    "support_agent": ["support.write"],
    "finance_manager": ["finance.write", "finance.read", "audit.read"],
    "customer": [],
}
NAMESPACE = UUID("14e57ad0-467c-4f88-a4e8-515a6c2a6b54")


def identifier(name):
    return str(uuid5(NAMESPACE, name))


def upgrade():
    for permission in PERMISSIONS:
        pid = identifier("permission:" + permission)
        op.execute(f"INSERT INTO identity.permissions(id,code) VALUES ('{pid}','{permission}')")
    for role, permissions in ROLES.items():
        rid = identifier("role:" + role)
        op.execute(f"INSERT INTO identity.roles(id,name) VALUES ('{rid}','{role}')")
        for permission in permissions:
            pid = identifier("permission:" + permission)
            assignment_id = identifier(role + ":" + permission)
            op.execute(
                "INSERT INTO identity.role_permissions(id,role_id,permission_id) "
                f"VALUES ('{assignment_id}','{rid}','{pid}')"
            )


def downgrade():
    raise RuntimeError("Role removal could revoke production access; explicit review required")
