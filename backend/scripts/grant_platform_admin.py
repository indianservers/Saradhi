"""Explicit local operator provisioning for an EXISTING user, no default credentials."""

import argparse
import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.application.common import add, audit
from backend.persistence import models as m
from backend.shared.auth import Principal
from backend.shared.database import create_database
from backend.shared.settings import get_settings


async def main(user_id):
    settings = get_settings()
    if settings.app_env != "development":
        raise SystemExit("This bootstrap command is restricted to local development")
    if "REPLACE_ME" in settings.database_url.get_secret_value():
        raise SystemExit("Authorized local DATABASE_URL is required")
    engine = create_database(settings)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False).begin() as db:
            user = await db.get(m.User, user_id)
            if not user or user.status != "active":
                raise SystemExit("Existing active user required")
            role = await db.scalar(select(m.Role).where(m.Role.name == "platform_super_admin"))
            if not role:
                raise SystemExit("Apply migrations first")
            existing = await db.scalar(
                select(m.RoleAssignment.id).where(
                    m.RoleAssignment.user_id == user.id,
                    m.RoleAssignment.role_id == role.id,
                    m.RoleAssignment.organization_id.is_(None),
                )
            )
            if not existing:
                await add(db, m.RoleAssignment, user_id=user.id, role_id=role.id)
                await audit(
                    db,
                    Principal(str(user.id), frozenset()),
                    "operator.grant_platform_admin",
                    user.id,
                    "explicit-local-operator",
                )
        print("Explicit local platform role is provisioned; no password was created or changed.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=UUID, required=True)
    asyncio.run(main(parser.parse_args().user_id))
