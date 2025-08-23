from pprint import pprint
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from dependencies.services import VacanciesServiceDep
from exceptions.repository_exceptions import (
    RegionRepositoryError,
    VacanciesRepositoryError,
)
from exceptions.service_exceptions import (
    HHAPIRequestError,
    InvalidLocationError,
    RegionNotFoundError,
    TVAPIRequestError,
    VacanciesHHNotFoundError,
    VacanciesNotFoundError,
    VacanciesTVNotFoundError,
    VacancyHHNotFoundError,
    VacancyNotFoundError,
    VacancyParseError,
    VacancyTVNotFoundError,
)
from schemas.vacancies import (
    VacanciesInfoSchema,
    VacanciesListSchema,
    VacanciesSearchRequest,
    VacancyDetailsOutSchema,
)

router = APIRouter()


@router.post(
    path='/search',
    summary=(
        'Получить количество найденных вакансий в '
        'заданном населенном пункте.'
    ),
    description=(
        'Возвращает количество найденных вакансий в '
        'заданном населенном пункте.'
    ),
    response_model=VacanciesInfoSchema
)
async def search_and_download_vacancies(
    data: VacanciesSearchRequest,
    vacancies_service: VacanciesServiceDep
) -> VacanciesInfoSchema:
    """
    Сохраняет и возвращает количество найденных вакансий в заданном населенном пункте.
    """
    try:
        validated_data = await vacancies_service.validation_and_get_region_data(
            location=data.location,
            region_code=data.region_code
        )
        vacancies_info = await vacancies_service.get_vacancies_info(
            location=validated_data.get('location'),
            region_data=validated_data.get('region_data')
        )
        return vacancies_info
    except (
        InvalidLocationError,
        RegionNotFoundError,
        RegionRepositoryError,
        TVAPIRequestError,
        HHAPIRequestError,
        VacanciesHHNotFoundError,
        VacanciesTVNotFoundError,
        VacancyParseError,
        VacanciesRepositoryError
    ) as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail(),
        )


@router.get(
    path='/list',
    summary='Получить список вакансий по локации с пагинацией',
    response_model=VacanciesListSchema,
)
async def get_vacancies(
    vacancies_service: VacanciesServiceDep,
    location: Annotated[
        str, Query(
            description='Наименование населенного пункта'
        )
    ],
    page: Annotated[
        int, Query(
            ge=1,
            description='Номер страницы.'
        )
    ] = 1,
    page_size: Annotated[
        int, Query(
            ge=1,
            le=100,
            description='Количество вакансий на странице.'
        )
    ] = 10,
):
    """"Возвращает список вакансий по локации с пагинацией."""
    try:
        return await vacancies_service.get_vacancies_by_location(
            location=location,
            page=page,
            page_size=page_size
        )
    except (
        VacanciesRepositoryError,
        VacanciesNotFoundError
    ) as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )


@router.get(
    path='/{vacancy_id}',
    summary='Получить информацию о вакансии по ID',
    response_model=VacancyDetailsOutSchema,
)
async def get_vacancy_by_id(
    vacancy_id: Annotated[
        str, Path(
            description='ID вакансии'
        )
    ],
    vacancies_service: VacanciesServiceDep,
):
    """
    Возвращает подробную информацию об одной вакансии по её ID.
    """
    try:
        return await vacancies_service.get_vacancy_details(
            vacancy_id=vacancy_id
        )
    except (
        TVAPIRequestError,
        HHAPIRequestError,
        VacancyParseError,
        VacancyHHNotFoundError,
        VacancyTVNotFoundError,
        VacancyNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
