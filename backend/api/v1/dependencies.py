from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.auth import Principal, current_principal
from backend.shared.database import session_scope


async def db_session(request: Request):
    async with session_scope(request.app.state.sessions) as session:
        yield session


DB = Annotated[AsyncSession, Depends(db_session, scope="function")]
Actor = Annotated[Principal, Depends(current_principal)]
