from uuid import uuid4

from sqlalchemy import select

from backend.application.common import add
from backend.persistence import models as m
from tests.integration.helpers import user


async def test_refund_approval_queue_is_limited_to_current_finance_scope(api):
    client, app = api
    finance_user = await user(client, app)
    outsider = await user(client, app)
    async with app.state.sessions.begin() as db:
        organization = await add(
            db, m.Organization, name="Finance queue " + uuid4().hex, owner_id=finance_user["id"]
        )
        await add(
            db,
            m.Membership,
            organization_id=organization.id,
            user_id=finance_user["id"],
            status="active",
        )
        role = await db.scalar(select(m.Role).where(m.Role.name == "finance_manager"))
        await add(
            db,
            m.RoleAssignment,
            user_id=finance_user["id"],
            role_id=role.id,
            organization_id=organization.id,
        )

    authorized = await client.get(
        "/api/v1/finance/authorized-organizations", headers=finance_user["headers"]
    )
    assert authorized.status_code == 200, authorized.text
    assert [row["id"] for row in authorized.json()["items"]] == [str(organization.id)]

    queue = await client.get(
        f"/api/v1/finance/refund-approvals?organization_id={organization.id}",
        headers=finance_user["headers"],
    )
    assert queue.status_code == 200, queue.text
    assert queue.json()["items"] == []

    denied = await client.get(
        f"/api/v1/finance/refund-approvals?organization_id={organization.id}",
        headers=outsider["headers"],
    )
    assert denied.status_code == 403

    missing_scope = await client.get(
        "/api/v1/finance/authorized-organizations", headers=outsider["headers"]
    )
    assert missing_scope.status_code == 200
    assert missing_scope.json()["items"] == []
