from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from dependencies.services import RegionServiceDep
from exceptions.repository_exceptions import RegionRepositoryError
from exceptions.service_exceptions import RegionsNotFoundError
from schemas.region import RegionSchema

router = APIRouter()


@router.get(
    path='/list',
    summary='Получить список всех регионов.',
    description='Возвращает полный список всех регионов.',
    response_model=list[RegionSchema]
)
async def list_regions(region_service: RegionServiceDep) -> list[RegionSchema]:
    """Возвращает полный список всех регионов."""
    try:
        return await region_service.get_region_list()
    except RegionRepositoryError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
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
    federal_district_code: Annotated[
        str, Query(
            description='Код федерального округа',
        )
    ],
) -> list[RegionSchema]:
    """Возвращает список регионов в заданном федеральном округе."""
    try:
        return await region_service.get_region_in_federal_district(
            federal_district_code=federal_district_code
        )
    except (RegionsNotFoundError, RegionRepositoryError) as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail(),
        )
