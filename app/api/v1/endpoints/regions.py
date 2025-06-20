from fastapi import APIRouter, HTTPException, Query, status

from core.config_logger import logger
from dependencies.services import RegionServiceDep
from exceptions.service_exceptions import RegionNotFoundError
from schemas.region import RegionSchema

router = APIRouter()


@router.get(
    path='/get-all',
    summary='Получить список всех регионов.',
    description='Возвращает полный список всех регионов.',
    response_model=list[RegionSchema]
)
async def list_regions(region_service: RegionServiceDep) -> list[RegionSchema]:
    """Возвращает полный список всех регионов."""
    try:
        return await region_service.get_region_list()
    except RegionNotFoundError as error:
        logger.error(f'Region not found: {error}')
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Regions not found'
        )


@router.get(
    path='/by-federal-districts',
    summary='Получить список регионов в заданном федеральном округе.',
    description=(
        'Возвращает список регионов в заданном федеральном округе.\n\n'
        'Код федерального округа. Возможные значения:\n\n'
        '* 30 — Центральный федеральный округ\n'
        '* 31 — Северо-Западный федеральный округ\n'
        '* 33 — Приволжский федеральный округ\n'
        '* 34 — Уральский федеральный округ\n'
        '* 38 — Северо-Кавказский федеральный округ\n'
        '* 40 — Южный федеральный округ\n'
        '* 41 — Сибирский федеральный округ\n'
        '* 42 — Дальневосточный федеральный округ'
    ),
    response_model=list[RegionSchema]
)
async def list_regions_by_federal_district(
    region_service: RegionServiceDep,
    federal_district_code: str = Query(
        ..., description='Код федерального округа'
    ),
) -> list[RegionSchema]:
    """Возвращает список регионов в заданном федеральном округе."""
    try:
        return await region_service.get_region_in_federal_district(
            federal_district_code=federal_district_code
        )
    except RegionNotFoundError as error:
        logger.error(
            f'No regions found in the submitted federal district: {error}'
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                'No regions found in the submitted federal district'
                f' with code: {federal_district_code}'
            )
        )
