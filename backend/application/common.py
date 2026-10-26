from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select

from backend.domain.rules import BusinessError
from backend.persistence import models as m
from backend.persistence.repositories import Repository


def now():
    return datetime.now(UTC)


async def add(session, model, **values):
    row = model(**values)
    session.add(row)
    await session.flush()
    return row


async def event(session, name, aggregate_id, request_id, **payload):
    return await add(
        session,
        m.Outbox,
        event_type=name,
        aggregate_id=aggregate_id,
        payload={str(k): str(v) for k, v in payload.items()},
        correlation_id=request_id,
    )


async def audit(session, actor, action, resource, request_id, organization_id=None, **changes):
    # Only explicit, non-sensitive state/version fields may enter safe_changes.
    allowed = {"previous", "current", "version", "decision"}
    return await add(
        session,
        m.AuditEvent,
        actor_id=UUID(actor.subject),
        action=action,
        resource_id=resource,
        correlation_id=request_id,
        organization_id=organization_id,
        safe_changes={k: str(v) for k, v in changes.items() if k in allowed},
    )


async def scoped(session, actor, permission, organization_id=None, city_id=None, branch_id=None):
    """Roles from token never grant database authority. Check current DB assignments."""
    user = await session.get(m.User, UUID(actor.subject))
    if not user or user.status != "active":
        raise BusinessError("forbidden", "Access denied", 403)
    query = (
        select(m.RoleAssignment, m.Role.name)
        .join(m.Role)
        .join(m.RolePermission, m.RolePermission.role_id == m.Role.id)
        .join(m.Permission, m.Permission.id == m.RolePermission.permission_id)
        .where(m.RoleAssignment.user_id == user.id, m.Permission.code == permission)
    )
    for assignment, role in (await session.execute(query)).all():
        if role == "platform_super_admin" and assignment.organization_id is None:
            return
        if (
            organization_id is None
            and city_id is not None
            and assignment.organization_id is None
            and assignment.city_id == city_id
            and assignment.branch_id is None
        ):
            return
        if (
            role == "city_manager"
            and assignment.city_id == city_id
            and assignment.branch_id is None
            and (organization_id is None or assignment.organization_id == organization_id)
        ):
            return
        if organization_id is None or assignment.organization_id != organization_id:
            continue
        membership = await session.scalar(
            select(m.Membership.id).where(
                m.Membership.organization_id == organization_id,
                m.Membership.user_id == user.id,
                m.Membership.status == "active",
            )
        )
        if not membership:
            continue
        if assignment.city_id is not None and assignment.city_id != city_id:
            continue
        if assignment.branch_id is not None and assignment.branch_id != branch_id:
            continue
        return
    raise BusinessError("forbidden", "Access denied for this resource scope", 403)


async def branch_scope(session, actor, branch_id, permission="merchant.write", lock=False):
    branch = await Repository(session).require(m.Branch, branch_id, lock=lock)
    await scoped(session, actor, permission, branch.organization_id, branch.city_id, branch.id)
    return branch


def owned(actor, owner_id):
    if str(owner_id) != actor.subject:
        raise BusinessError("forbidden", "Access denied", 403)
