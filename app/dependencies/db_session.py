from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Генератор для создания сессии базы данных."""
    async with async_session_factory() as db_session:
        yield db_session


DbSessionDep = Annotated[AsyncSession, Depends(get_db_session)]
