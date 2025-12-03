from pprint import pformat

from fastapi import FastAPI, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1 import router as v1_router
from core.config_logger import logger
from core.limiter import limiter
from db.session import async_session_factory
from dependencies.services import check_db_connection
from exceptions.service_exceptions import RegionStartupError
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
    except RegionStartupError as error:
        logger.critical(
            f'An error occurred while loading region data: {error}.'
            'The application will be stopped.'
        )
        raise
    logger.info('>>> Application STARTED successfully <<<')
    yield
    logger.info('>>> Application STOPPING <<<')

app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Перехватывает ошибки валидации Pydantic, логирует их и возвращает
    стандартный ответ 422.
    """
    error_details = exc.errors()
    logger.warning(
        "Ошибка валидации для запроса: %s %s. Детали: %s",
        request.method,
        request.url.path,
        pformat(error_details),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": error_details},
    )


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(v1_router, prefix='/api/v1')
