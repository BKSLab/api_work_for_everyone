import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from dependencies.services import RegionServiceDep
from exceptions.regions import RegionsByFDNotFoundError
from exceptions.repositories import RegionRepositoryError
from exceptions.services import RegionServiceError
from schemas.region import RegionSchema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    path="/list",
    status_code=status.HTTP_200_OK,
    summary="Получить список всех регионов",
    description="Возвращает полный список всех регионов.",
    responses={
        200: {"description": "Данные о регионах успешно получены."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    response_model=list[RegionSchema],
)
async def list_regions(region_service: RegionServiceDep) -> list[RegionSchema]:
    """Возвращает полный список всех регионов.

    Args:
        region_service: Сервис для работы с регионами.

    Returns:
        Полный список всех регионов.
    """
    logger.info("Начало обработки /regions/list.")
    try:
        region_data = await region_service.get_region_list()
        logger.info("Успешное завершение /regions/list.")

        return region_data
    except (RegionRepositoryError, RegionServiceError) as error:
        logger.exception(
            "Ошибка при получении списка регионов: %s",
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.get(
    path="/by-federal-districts",
    status_code=status.HTTP_200_OK,
    summary="Получить список регионов в заданном федеральном округе",
    description=(
        "Возвращает список регионов в заданном федеральном округе.\n\n"
        "Код федерального округа. Возможные значения:\n\n"
        "* 30 — Центральный федеральный округ\n"
        "* 31 — Северо-Западный федеральный округ\n"
        "* 33 — Приволжский федеральный округ\n"
        "* 34 — Уральский федеральный округ\n"
        "* 38 — Северо-Кавказский федеральный округ\n"
        "* 40 — Южный федеральный округ\n"
        "* 41 — Сибирский федеральный округ\n"
        "* 42 — Дальневосточный федеральный округ"
    ),
    responses={
        200: {"description": "Данные о регионах успешно получены."},
        404: {
            "description": "Данные о регионах в заданном федеральном округе не найдены."
        },
        500: {"description": "Внутренняя ошибка сервера."},
    },
    response_model=list[RegionSchema],
)
async def list_regions_by_federal_district(
    region_service: RegionServiceDep,
    federal_district_code: Annotated[
        str,
        Query(
            description="Код федерального округа",
        ),
    ],
) -> list[RegionSchema]:
    """Возвращает список регионов в заданном федеральном округе.

    Args:
        region_service: Сервис для работы с регионами.
        federal_district_code: Код федерального округа.

    Returns:
        Cписок регионов в заданном федеральном округе.
    """
    logger.info(
        "Начало обработки /regions/by-federal-districts для округа %s.",
        federal_district_code,
    )
    try:
        region_data = await region_service.get_region_in_federal_district(
            federal_district_code=federal_district_code
        )
        logger.info(
            "Успешное завершение /regions/by-federal-districts для округа %s.",
            federal_district_code,
        )

        return region_data
    except (
        RegionRepositoryError,
        RegionsByFDNotFoundError,
        RegionServiceError,
    ) as error:
        logger.exception(
            "Ошибка при получении регионов для округа %s: %s",
            federal_district_code,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        )
