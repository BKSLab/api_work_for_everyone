import logging

from fastapi import APIRouter, HTTPException, status

from dependencies.services import RegionServiceDep
from exceptions.repositories import RegionRepositoryError
from exceptions.services import RegionServiceError
from schemas.region import FederalDistrictSchema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    path="/list",
    status_code=status.HTTP_200_OK,
    summary="Получить список всех федеральных округов",
    description="Возвращает полный список всех федеральных округов.",
    operation_id="getFederalDistrictsList",
    response_description="Полный список федеральных округов",
    responses={
        200: {
            "description": "Данные о федеральных округах успешно получены.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "Приволжский федеральный округ",
                            "code": "33",
                        },
                        {
                            "name": "Центральный федеральный округ",
                            "code": "30",
                        },
                    ]
                }
            },
        },
        401: {
            "description": "API-ключ отсутствует или невалиден.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid API key."}
                }
            },
        },
        403: {
            "description": "API-ключ просрочен или деактивирован.",
            "content": {
                "application/json": {
                    "example": {"detail": "API key has expired."}
                }
            },
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {
                "application/json": {
                    "example": {"detail": "A database error occurred while processing region data."}
                }
            },
        },
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
    logger.info("🚀 Запрос GET /federal-districts/list.")
    try:
        region_data = await region_service.get_federal_districts_list()
        logger.info("✅ Запрос GET /federal-districts/list выполнен.")

        return region_data
    except (RegionRepositoryError, RegionServiceError) as error:
        logger.exception(
            "❌ Ошибка при получении списка федеральных округов. Детали: %s",
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)
