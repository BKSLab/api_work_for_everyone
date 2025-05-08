from fastapi.concurrency import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.custom_exceptions import RegionDataLoadError
from services.region_service import RegionService
from repositories.region_repository import RegionRepository
from db.session import async_session_factory
from core.config_logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Функция управления жизненным циклом приложения."""
    logger.info(">>> Lifespan STARTED <<<")
    try:
        async with async_session_factory() as db_session:
            db_session: AsyncSession
            region_service = RegionService(
                region_repository=RegionRepository(db_session=db_session)
            )
            await region_service.preload_region_data_if_empty()
    except RegionDataLoadError as error:
        logger.critical(
            f'An error occurred while loading region data: {error}.'
            'The application will be stopped.'
        )
        raise
    yield
    logger.info(">>> Lifespan FINISHED <<<")

app = FastAPI(lifespan=lifespan)

# app.include_router(file_router)
# https://fastapi.tiangolo.com/advanced/settings/#pydantic-settings