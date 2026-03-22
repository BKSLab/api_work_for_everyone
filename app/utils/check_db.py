import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def check_db_connection(db_session: AsyncSession) -> bool:
    """Проверяет доступность БД и выполнение простого запроса."""
    try:
        await db_session.execute(text("SELECT 1"))
    except Exception as error:
        logger.error("❌ Ошибка подключения к базе данных: %s", error)
        raise RuntimeError('Проверка подключения к базе данных не прошла.') from error
