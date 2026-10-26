"""Small explicit repositories; never exposed as generic public CRUD."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.rules import BusinessError


class Repository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def require(self, model, identifier: UUID, *, lock=False):
        query = select(model).where(model.id == identifier)
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        result = await self.session.scalar(query)
        if result is None:
            raise BusinessError("not_found", "Resource not found", 404)
        return result

    async def page(self, model, predicates, *, after: UUID | None, limit: int):
        query = select(model).where(*predicates).order_by(model.id).limit(limit + 1)
        if after:
            query = query.where(model.id > after)
        rows = list((await self.session.scalars(query)).all())
        return rows[:limit], rows[limit - 1].id if len(rows) > limit else None
