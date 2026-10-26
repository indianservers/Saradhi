from uuid import uuid4

from sqlalchemy import func, select

from backend.persistence import models as m
from tests.integration.helpers import user, world


async def test_branch_csv_import_is_scoped_previewed_idempotent_and_pending(api):
    client, app = api
    state = await world(client, app, 1)
    admin = state["admin"]
    branch = state["shops"][0]["branch"]
    source_reference = "migration-store-" + uuid4().hex
    branch_name = "Bulk Market " + uuid4().hex[:12]
    content = (
        "external_ref,brand_id,city_id,branch_name,latitude,longitude\n"
        f"{source_reference},{branch['brand_id']},{state['city']['id']},"
        f"{branch_name},17.4000000,78.4000000\n"
    )
    headers = {
        **admin["headers"],
        "content-type": "text/csv; charset=utf-8",
        "x-bulk-entity": "branches",
        "idempotency-key": "branch-import-" + uuid4().hex,
    }
    uploaded = await client.post("/api/v1/bulk/imports", content=content, headers=headers)
    assert uploaded.status_code == 201, uploaded.text
    job = uploaded.json()
    assert job["status"] == "VALIDATED"
    if job["valid_count"] != 1:
        issues = await client.get(
            f"/api/v1/bulk/imports/{job['id']}/errors", headers=admin["headers"]
        )
        assert job["valid_count"] == 1, issues.text

    preview = await client.post(
        f"/api/v1/bulk/imports/{job['id']}/dry-run", headers=admin["headers"]
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["rows"][0]["branch_name"] == branch_name
    assert preview.json()["rows"][0]["status"] == "valid"

    committed = await client.post(
        f"/api/v1/bulk/imports/{job['id']}/commit", headers=admin["headers"]
    )
    assert committed.status_code == 200, committed.text
    assert committed.json()["status"] == "COMPLETED"
    assert committed.json()["created_count"] == 1
    repeated = await client.post(
        f"/api/v1/bulk/imports/{job['id']}/commit", headers=admin["headers"]
    )
    assert repeated.status_code == 200
    assert repeated.json()["created_count"] == 1

    async with app.state.sessions() as db:
        imported = await db.scalar(select(m.Branch).where(m.Branch.name == branch_name))
        assert imported is not None
        assert imported.status == "pending"
        assert imported.accepting_orders is False
        assert (
            await db.scalar(
                select(func.count())
                .select_from(m.BulkExternalRef)
                .where(
                    m.BulkExternalRef.entity == "branch",
                    m.BulkExternalRef.source_key == source_reference,
                )
            )
            == 1
        )

    replay = await client.post("/api/v1/bulk/imports", content=content, headers=headers)
    assert replay.status_code == 201
    assert replay.json()["id"] == job["id"]

    export = await client.post(
        "/api/v1/bulk/exports",
        json={"entity": "branches", "city_id": state["city"]["id"], "limit": 500},
        headers=admin["headers"],
    )
    assert export.status_code == 200, export.text
    assert branch_name in export.text
    assert "no-store" in export.headers["cache-control"]
    assert "public" not in export.headers["cache-control"]

    stranger = await user(client, app)
    hidden = await client.get(f"/api/v1/bulk/imports/{job['id']}", headers=stranger["headers"])
    assert hidden.status_code == 404


async def test_bulk_import_rejects_user_without_merchant_write_scope(api):
    client, app = api
    stranger = await user(client, app)
    response = await client.post(
        "/api/v1/bulk/imports",
        content="external_ref,brand_id,city_id,branch_name,latitude,longitude\n",
        headers={
            **stranger["headers"],
            "content-type": "text/csv",
            "x-bulk-entity": "branches",
            "idempotency-key": "unauthorized-import-0001",
        },
    )
    assert response.status_code == 403
