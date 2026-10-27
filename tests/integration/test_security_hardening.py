from datetime import timedelta
from uuid import UUID, uuid4

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.application.common import add, now
from backend.persistence import models as m
from tests.integration.helpers import user, world


async def test_kitchen_role_is_branch_scoped_and_cannot_manage_merchant_or_inventory(api):
    client, app = api
    state = await world(client, app, count=2)
    shop_a, shop_b = state["shops"]
    staff = await user(client, app)
    assigned = await client.post(
        f"/api/v1/organizations/{shop_a['organization']['id']}/members",
        json={
            "user_id": staff["id"],
            "role": "kitchen_operator",
            "branch_id": shop_a["branch"]["id"],
        },
        headers=shop_a["merchant"]["headers"],
    )
    assert assigned.status_code == 201, assigned.text

    stations_url = f"/api/v1/merchant/branches/{shop_a['branch']['id']}/kitchen/stations"
    own_stations = await client.get(stations_url, headers=staff["headers"])
    assert own_stations.status_code == 200
    created_station = await client.post(
        stations_url,
        json={"name": "Kitchen line " + uuid4().hex[:8], "is_packaging": False},
        headers=staff["headers"],
    )
    assert created_station.status_code == 201, created_station.text

    foreign_stations = await client.get(
        f"/api/v1/merchant/branches/{shop_b['branch']['id']}/kitchen/stations",
        headers=staff["headers"],
    )
    merchant_admin = await client.get(
        f"/api/v1/merchant/branches/{shop_a['branch']['id']}/catalog",
        headers=staff["headers"],
    )
    inventory = await client.get(
        f"/api/v1/inventory/branches/{shop_a['branch']['id']}",
        headers=staff["headers"],
    )
    assert foreign_stations.status_code == 403
    assert merchant_admin.status_code == 403
    assert inventory.status_code == 403

    escalated_user = await user(client, app)
    escalation = await client.post(
        f"/api/v1/organizations/{shop_a['organization']['id']}/members",
        json={
            "user_id": escalated_user["id"],
            "role": "platform_super_admin",
            "branch_id": shop_a["branch"]["id"],
        },
        headers=shop_a["merchant"]["headers"],
    )
    assert escalation.status_code == 422
    cross_company_assignment = await client.post(
        f"/api/v1/organizations/{shop_a['organization']['id']}/members",
        json={
            "user_id": staff["id"],
            "role": "branch_manager",
            "branch_id": shop_a["branch"]["id"],
            "organization_id": shop_b["organization"]["id"],
        },
        headers=shop_a["merchant"]["headers"],
    )
    assert cross_company_assignment.status_code == 422
    async with app.state.sessions() as db:
        role_assignment = await db.scalar(
            select(m.RoleAssignment.id)
            .join(m.Role, m.Role.id == m.RoleAssignment.role_id)
            .where(
                m.RoleAssignment.user_id == UUID(escalated_user["id"]),
                m.Role.name == "platform_super_admin",
            )
        )
        audit_row = await db.scalar(
            select(m.AuditEvent).where(
                m.AuditEvent.action == "organization.member_role_assigned",
                m.AuditEvent.resource_id == UUID(staff["id"]),
            )
        )
    assert role_assignment is None
    assert audit_row is not None
    assert str(audit_row.organization_id) == shop_a["organization"]["id"]


async def test_public_branch_windows_and_prices_hide_inactive_or_pending_resources(api):
    client, app = api
    state = await world(client, app, count=1)
    active_branch = state["shops"][0]["branch"]
    active_windows = await client.get(f"/api/v1/merchants/branches/{active_branch['id']}/windows")
    active_prices = await client.get(f"/api/v1/merchants/branches/{active_branch['id']}/prices")
    assert active_windows.status_code == active_prices.status_code == 200
    assert active_windows.json()["items"]
    assert active_prices.json()["items"]

    pending = await client.post(
        "/api/v1/merchants/branches",
        json={
            "brand_id": state["shops"][0]["branch"]["brand_id"],
            "city_id": state["city"]["id"],
            "name": "Pending branch " + uuid4().hex[:8],
            "latitude": "17.385",
            "longitude": "78.4867",
        },
        headers=state["shops"][0]["merchant"]["headers"],
    )
    assert pending.status_code == 201, pending.text
    async with app.state.sessions.begin() as db:
        await add(
            db,
            m.Window,
            branch_id=pending.json()["id"],
            starts_at=now() + timedelta(days=1),
            ends_at=now() + timedelta(days=1, hours=1),
            capacity=20,
        )
    hidden_window = await client.get(f"/api/v1/merchants/branches/{pending.json()['id']}/windows")
    hidden_prices = await client.get(f"/api/v1/merchants/branches/{pending.json()['id']}/prices")
    assert hidden_window.status_code == hidden_prices.status_code == 404


async def test_shared_request_limit_ignores_untrusted_forwarded_for(api):
    _client, app = api
    app.state.settings.api_requests_per_minute = 30
    transport = ASGITransport(app=app, client=(f"198.51.100.{(uuid4().int % 200) + 1}", 32123))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        statuses = []
        for index in range(31):
            response = await client.get(
                "/api/v1/roles",
                headers={"X-Forwarded-For": f"203.0.113.{(index % 200) + 1}"},
            )
            statuses.append(response.status_code)
            if response.status_code == 429:
                assert response.headers["retry-after"] == "60"
                assert response.json()["error"]["code"] == "rate_limited"
        assert statuses.count(429) == 1


async def test_login_throttle_is_temporary_and_scoped_to_account_and_network(api):
    client, app = api
    app.state.settings.auth_rate_limit_per_minute = 1
    transport = ASGITransport(
        app=app,
        client=(f"192.0.2.{(uuid4().int % 200) + 1}", 32124),
    )
    async with AsyncClient(transport=transport, base_url="http://test") as isolated_client:
        email = f"security-{uuid4().hex}@example.test"
        registered = await isolated_client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Security-test!123"},
        )
        assert registered.status_code == 201
        first = await isolated_client.post(
            "/api/v1/auth/login", json={"email": email, "password": "incorrect-password"}
        )
        second = await isolated_client.post(
            "/api/v1/auth/login", json={"email": email, "password": "incorrect-password"}
        )
    assert first.status_code == 401
    assert second.status_code == 429
    assert second.headers["retry-after"] == "60"
