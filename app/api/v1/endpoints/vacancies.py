from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from core.config_logger import logger
from dependencies.services import VacanciesServiceDep
from exceptions.repository_exceptions import RegionRepositoryError
from exceptions.service_exceptions import (
    InvalidLocationError,
    RegionNotFoundError,
)

router = APIRouter()


@router.get(
    path='/search',
    summary=(
        'Получить количество найденных вакансий в '
        'заданном населенном пункте.'
    ),
    description=(
        'Возвращает количество найденных вакансий в '
        'заданном населенном пункте.'
    ),
    # response_model=list[RegionSchema]
)
async def search_and_download_vacancies(
    region_code: Annotated[
        str, Query(
            description='Код региона',
        )
    ],
    location: Annotated[
        str, Query(
            description='Наименование населенного пункта',
        )
    ],
    vacancies_service: VacanciesServiceDep
):
    """
    Возвращает количество найденных вакансий в заданном населенном пункте.
    """
    logger.info(f'location: {location}')
    logger.info(f'region_name: {region_code}')    
    try:
        validated_data = await vacancies_service.validation_and_get_region_data(
            location=location, region_code=region_code
        )
    except (
        InvalidLocationError,
        RegionNotFoundError,
        RegionRepositoryError
    ) as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail(),
        )
    # вызываем метод получения информации о вакансиях
    result = await vacancies_service.get_vacancies_from_tv(
        location=validated_data.get('location'),
        region_data=validated_data.get('region_data')
    )
    # except InvalidLocationError as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #         detail=str(e)
    #     )
    # except InvalidRegionCodeError as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=str(e)
    #     )