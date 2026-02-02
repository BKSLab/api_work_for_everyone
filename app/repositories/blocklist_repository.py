import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.models.blocklist import BlockedToken
from exceptions.repositories import BlocklistRepositoryError

logger = logging.getLogger(__name__)


class BlocklistRepository:
    """Репозиторий для работы с черным списком токенов в базе данных."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_token_to_blocklist(self, jti: str, exp: datetime) -> None:
        """Добавляет JTI токена в черный список."""
        try:
            blocked_token = BlockedToken(jti=jti, exp=exp)
            self.db_session.add(blocked_token)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise BlocklistRepositoryError(
                error_details="Error adding token to blocklist."
            ) from error

    async def is_token_blocked(self, jti: str) -> bool:
        """Проверяет, находится ли JTI токена в черном списке."""
        try:
            result = await self.db_session.execute(
                select(BlockedToken).where(BlockedToken.jti == jti)
            )
            return result.scalar_one_or_none() is not None
        except (SQLAlchemyError, Exception) as error:
            raise BlocklistRepositoryError(
                error_details="Error checking if token is in blocklist."
            ) from error
