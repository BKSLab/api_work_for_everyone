import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from dependencies.services import VacanciesServiceDep
from exceptions.api_clients import HHAPIRequestError, TVAPIRequestError
from exceptions.parsing_vacancies import VacancyParseError
from exceptions.regions import LocationValidationError, RegionNotFoundError
from exceptions.repositories import (
    RegionRepositoryError,
    VacanciesRepositoryError,
)
from exceptions.services import RegionServiceError, VacanciesServiceError
from exceptions.vacancies import VacancyNotFoundError
from schemas.vacancies import (
    VacanciesInfoSchema,
    VacanciesListSchema,
    VacanciesSearchRequest,
    VacancyDetailsOutSchema,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    path="/search",
    status_code=status.HTTP_201_CREATED,
    summary="Поиск и сохранение вакансий",
    description="Ищет и сохраняет вакансии из внешних источников по населенному пункту и коду региона.",
    responses={
        201: {
            "description": "Вакансии успешно найдены и сохранены, возвращается информация о количестве.",
        },
        400: {
            "description": "Ошибка валидации: неверные данные в запросе.",
        },
        404: {
            "description": "Регион с указанным кодом не найден.",
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
        },
    },
    response_model=VacanciesInfoSchema,
)
async def search_and_download_vacancies(
    data: VacanciesSearchRequest,
    vacancies_service: VacanciesServiceDep,
) -> VacanciesInfoSchema:
    """Ищет, сохраняет и возвращает количество найденных вакансий.

    Args:
        data: Модель с данными для поиска (населенный пункт, код региона).
        vacancies_service: Сервис для работы с вакансиями.

    Returns:
        Модель с информацией о количестве найденных вакансий.
    """
    logger.info(
        "Начало обработки /search для '%s' (регион %s).",
        data.location,
        data.region_code,
    )
    try:
        # 1. Валидация и получение данных по региону
        validated_data = await vacancies_service.validation_and_get_region_data(
            location=data.location, region_code=data.region_code
        )

        # 2. Запрос вакансий и сохранение их в БД
        vacancies_info = await vacancies_service.get_vacancies_info(
            location=validated_data.get("location"),
            region_data=validated_data.get("region_data"),
        )
        logger.info("Успешное завершение /search для '%s'.", data.location)
        return vacancies_info
    except (
        LocationValidationError,
        RegionNotFoundError,
        RegionRepositoryError,
        RegionServiceError,
        VacanciesServiceError,
        VacanciesRepositoryError,
    ) as error:
        logger.exception(
            "Ошибка при поиске и сохранении вакансий. location: %s, region_code: %s, error: %s",
            data.location,
            data.region_code,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.get(
    path="/list",
    status_code=status.HTTP_200_OK,
    summary="Получение списка вакансий с пагинацией",
    description="Возвращает список сохраненных вакансий с пагинацией для заданного населенного пункта.",
    responses={
        200: {
            "description": "Список вакансий успешно получен.",
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
        },
    },
    response_model=VacanciesListSchema,
)
async def get_vacancies(
    vacancies_service: VacanciesServiceDep,
    location: Annotated[str, Query(description="Наименование населенного пункта")],
    page: Annotated[int, Query(ge=1, description="Номер страницы.")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Количество вакансий на странице.")
    ] = 10,
):
    """Возвращает список вакансий по населенному пункту с пагинацией.

    Args:
        vacancies_service: Сервис для работы с вакансиями.
        location: Наименование населенного пункта для фильтрации.
        page: Номер страницы для пагинации.
        page_size: Количество вакансий на странице.

    Returns:
        Модель со списком вакансий и информацией о пагинации.
    """
    logger.info(
        "Начало обработки /list для '%s' (страница %s, размер %s).",
        location,
        page,
        page_size,
    )
    try:
        vacancy_data = await vacancies_service.get_vacancies_by_location(
            location=location, page=page, page_size=page_size
        )
        logger.info("Успешное завершение /list для '%s'.", location)
        return vacancy_data
    except (VacanciesRepositoryError, VacanciesServiceError) as error:
        logger.exception(
            "Ошибка при получении данных вакансий. location: %s, страница: %s, размер страницы: %s, error: %s",
            location,
            page,
            page_size,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.get(
    path="/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Получение детальной информации о вакансии",
    description="Возвращает подробную информацию о конкретной вакансии по её ID.",
    responses={
        200: {
            "description": "Детальная информация о вакансии успешно получена.",
        },
        404: {
            "description": "Вакансия с указанным ID не найдена.",
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
        },
    },
    response_model=VacancyDetailsOutSchema,
)
async def get_vacancy_by_id(
    vacancy_id: Annotated[str, Path(description="ID вакансии")],
    vacancies_service: VacanciesServiceDep,
):
    """Возвращает подробную информацию о вакансии по её ID.

    Args:
        vacancy_id: Уникальный идентификатор вакансии.
        vacancies_service: Сервис для работы с вакансиями.

    Returns:
        Модель с детальной информацией о вакансии.
    """
    logger.info("Начало обработки запроса для вакансии с ID %s.", vacancy_id)
    try:
        vacancy = await vacancies_service.get_vacancy_details(vacancy_id=vacancy_id)
        logger.info("Успешное завершение запроса для вакансии с ID %s.", vacancy_id)
        return vacancy
    except (
        VacanciesRepositoryError,
        VacancyNotFoundError,
        VacanciesServiceError,
        VacancyParseError,
        HHAPIRequestError,
        TVAPIRequestError,
    ) as error:
        logger.exception(
            "Ошибка при получении информации по вакансии. vacancy_id: %s, error: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)
