from fastapi import APIRouter, HTTPException

from schemas.vacancies import VacanciesInfoSchema, VacanciesSearchRequest
from dependencies.services import VacanciesServiceDep
from exceptions.repository_exceptions import (
    RegionRepositoryError,
    VacanciesRepositoryError
)
from exceptions.service_exceptions import (
    HHAPIRequestError,
    InvalidLocationError,
    RegionNotFoundError,
    TVAPIRequestError,
    VacanciesHHNotFoundError,
    VacanciesTVNotFoundError,
    VacancyParseError,
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
