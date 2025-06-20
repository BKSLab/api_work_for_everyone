from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import router as v1_router
from core.config_logger import logger
from db.session import async_session_factory
from dependencies.services import check_db_connection
from exceptions.service_exceptions import RegionDataLoadError
from repositories.region_repository import RegionRepository
from services.region_service import RegionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Функция управления жизненным циклом приложения."""
    logger.info('>>> Lifespan STARTED <<<')
    try:
        async with async_session_factory() as db_session:
            db_session: AsyncSession
            if not await check_db_connection(db_session):
                raise RuntimeError('Database connection test failed')
            region_service = RegionService(
                region_repository=RegionRepository(db_session=db_session)
            )
            await region_service.preload_region_data()
    except RegionDataLoadError as error:
        logger.critical(
            f'An error occurred while loading region data: {error}.'
            'The application will be stopped.'
        )
        raise
    logger.info('>>> Application STARTED successfully <<<')
    yield
    logger.info('>>> Application STOPPING <<<')

app = FastAPI(lifespan=lifespan)

app.include_router(v1_router, prefix='/api/v1')
