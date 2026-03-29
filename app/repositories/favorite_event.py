import logging

from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.favorite_event import FavoriteEvent

logger = logging.getLogger(__name__)


class FavoriteEventRepository:
    """Репозиторий для записи событий добавления/удаления избранных вакансий."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def save_event(self, data: dict) -> None:
        """Сохраняет событие. Не поднимает исключений — только логирует."""
        try:
            stmt = insert(FavoriteEvent).values(**data)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.warning("⚠️ Не удалось сохранить событие избранного: %s", error)
