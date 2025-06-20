from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config_logger import logger
from dependencies.repositories import RegionRepositoryDep
from services.region_service import RegionService


async def get_region_service(region_repository: RegionRepositoryDep) -> RegionService:
    """Генератор для создания сессии базы данных."""
    return RegionService(region_repository)


RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]


async def check_db_connection(db_session: AsyncSession) -> bool:
    """Проверяет доступность БД и выполнение простого запроса."""
    try:
        await db_session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f'Database connection check failed: {str(e)}')
        return False
