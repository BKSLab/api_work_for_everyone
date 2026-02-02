import logging

from fastapi import APIRouter, status, HTTPException

from exceptions.repositories import RegionRepositoryError
from exceptions.services import RegionServiceError
from dependencies.services import RegionServiceDep
from schemas.region import FederalDistrictSchema


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    path="/list",
    status_code=status.HTTP_200_OK,
    summary="Получить список всех федеральных округов",
    description="Возвращает полный список всех федеральных округов.",
    responses={
        200: {"description": "Данные о федеральных округов успешно получены."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    response_model=list[FederalDistrictSchema],
)
async def list_federal_districts(region_service: RegionServiceDep) -> list[FederalDistrictSchema]:
    """Возвращает полный список всех федеральных округов.

    Args:
        region_service: Сервис для работы с федеральными округами.

    Returns:
        Полный список всех федеральных округов.
    """
    logger.info("Начало обработки /federal-districts/list.")
    try:
        region_data = await region_service.get_federal_districts_list()
        logger.info("Успешное завершение /federal-districts/list.")

        return region_data
    except (RegionRepositoryError, RegionServiceError) as error:
        logger.exception(
            "Ошибка при получении списка федеральных округов: %s",
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)
