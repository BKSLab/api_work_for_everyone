import logging
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from dependencies.services import VacanciesServiceDep
from exceptions.api_clients import HHAPIRequestError, TVAPIRequestError
from exceptions.parsing_vacancies import VacancyParseError
from exceptions.regions import LocationValidationError, RegionNotFoundError
from exceptions.repositories import (
    FavoritesRepositoryError,
    RegionRepositoryError,
    VacanciesRepositoryError,
)
from exceptions.services import RegionServiceError, VacanciesServiceError
from exceptions.vacancies import VacancyNotFoundError
from schemas.vacancies import (
    VacanciesInfoSchema,
    VacanciesListSchema,
    VacanciesSearchRequest,
    VacancySchema,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    path="/search",
    status_code=status.HTTP_201_CREATED,
    summary="Поиск и сохранение вакансий",
    description="Ищет и сохраняет вакансии из внешних источников по населенному пункту и коду региона.",
    operation_id="searchAndDownloadVacancies",
    response_description="Информация о количестве найденных и сохранённых вакансий",
    responses={
        201: {
            "description": "Вакансии успешно найдены и сохранены.",
            "content": {
                "application/json": {
                    "example": {
                        "all_vacancies_count": 142,
                        "vacancies_count_tv": 58,
                        "vacancies_count_hh": 84,
                        "error_request_hh": False,
                        "error_request_tv": False,
                        "error_details_hh": "",
                        "error_details_tv": "",
                        "location": "Ижевск",
                        "region_name": "Удмуртская Республика",
                    }
                }
            },
        },
        400: {
            "description": "Ошибка валидации: неверные данные в запросе.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid location value."}
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
        404: {
            "description": "Регион с указанным кодом не найден.",
            "content": {
                "application/json": {
                    "example": {"detail": "Region with code '99' not found."}
                }
            },
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {
                "application/json": {
                    "example": {"detail": "A database error occurred while processing vacancies data."}
                }
            },
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
        "🚀 Запрос POST /search. Населённый пункт: '%s', код региона: %s.",
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
        logger.info("✅ Запрос POST /search выполнен. Населённый пункт: '%s'.", data.location)
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
            "❌ Ошибка при поиске вакансий. Населённый пункт: %s, код региона: %s. Детали: %s",
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
    operation_id="getVacanciesList",
    response_description="Список вакансий с информацией о пагинации",
    responses={
        200: {
            "description": "Список вакансий успешно получен.",
            "content": {
                "application/json": {
                    "example": {
                        "total": 142,
                        "page": 1,
                        "page_size": 10,
                        "items": [
                            {
                                "vacancy_id": "12345",
                                "vacancy_name": "Python-разработчик",
                                "location": "Ижевск",
                                "vacancy_url": "https://example.com/vacancy/12345",
                                "vacancy_source": "hh.ru",
                                "status": "actual",
                                "description": "Разработка backend-сервисов.",
                                "salary": "от 150 000 руб.",
                                "employer_name": "ООО Рога и Копыта",
                                "employer_location": "Москва",
                                "employer_phone": "+7 (495) 123-45-67",
                                "employer_code": "9876",
                                "employer_email": "",
                                "contact_person": "",
                                "employment": "Полная занятость",
                                "schedule": "Удалённая работа",
                                "work_format": "",
                                "experience_required": "1-3 года",
                                "requirements": "",
                                "category": "IT",
                                "social_protected": "",
                                "is_favorite": False,
                            }
                        ],
                    }
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
                    "example": {"detail": "A database error occurred while processing vacancies data."}
                }
            },
        },
    },
    response_model=VacanciesListSchema,
)
async def get_vacancies(
    vacancies_service: VacanciesServiceDep,
    location: Annotated[str, Query(description="Наименование населенного пункта")],
    user_id: Annotated[Optional[str], Query(description="Идентификатор пользователя во внешней системе")] = None,
    page: Annotated[int, Query(ge=1, description="Номер страницы.")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=100, description="Количество вакансий на странице.")
    ] = 10,
    keyword: Annotated[Optional[str], Query(description="Ключевое слово для поиска в названии и описании вакансии.")] = None,
    source: Annotated[Optional[Literal["hh.ru", "trudvsem.ru"]], Query(description="Фильтр по источнику вакансий.")] = None,
):
    """Возвращает список вакансий по населенному пункту с пагинацией.

    Args:
        vacancies_service: Сервис для работы с вакансиями.
        location: Наименование населенного пункта для фильтрации.
        user_id: Идентификатор пользователя во внешней системе, опциональное поле.
        page: Номер страницы для пагинации.
        page_size: Количество вакансий на странице.
        keyword: Ключевое слово для поиска по названию и описанию вакансии.
        source: Фильтр по источнику ('hh.ru' или 'trudvsem.ru').

    Returns:
        Модель со списком вакансий и информацией о пагинации.
    """
    logger.info(
        "🚀 Запрос GET /list. Населённый пункт: '%s', страница: %s, размер: %s, ключевое слово: %s, источник: %s.",
        location,
        page,
        page_size,
        keyword,
        source,
    )
    try:
        vacancy_data = await vacancies_service.get_vacancies_by_location(
            location=location, page=page, page_size=page_size,
            user_id=user_id, keyword=keyword, source=source,
        )
        logger.info("✅ Запрос GET /list выполнен. Населённый пункт: '%s'.", location)
        return vacancy_data
    except (VacanciesRepositoryError, FavoritesRepositoryError, VacanciesServiceError) as error:
        logger.exception(
            "❌ Ошибка при получении вакансий. Населённый пункт: %s, страница: %s, размер: %s, ключевое слово: %s, источник: %s. Детали: %s",
            location,
            page,
            page_size,
            keyword,
            source,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.get(
    path="/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Получение детальной информации о вакансии",
    description="Возвращает подробную информацию о конкретной вакансии по её ID.",
    operation_id="getVacancyById",
    response_description="Детальная информация о вакансии",
    responses={
        200: {
            "description": "Детальная информация о вакансии успешно получена.",
            "content": {
                "application/json": {
                    "example": {
                        "vacancy_id": "12345",
                        "vacancy_name": "Python-разработчик",
                        "location": "Ижевск",
                        "vacancy_url": "https://example.com/vacancy/12345",
                        "vacancy_source": "hh.ru",
                        "status": "actual",
                        "description": "Разработка backend-сервисов на Python.",
                        "salary": "от 150 000 руб.",
                        "employer_name": "ООО Рога и Копыта",
                        "employer_location": "Москва",
                        "employer_phone": "+7 (495) 123-45-67",
                        "employer_code": "9876",
                        "employer_email": "hr@example.com",
                        "contact_person": "Иванов И.И.",
                        "employment": "Полная занятость",
                        "schedule": "Удалённая работа",
                        "work_format": "Дистанционная работа",
                        "experience_required": "1-3 года",
                        "requirements": "Python, FastAPI, PostgreSQL",
                        "category": "IT",
                        "social_protected": "",
                        "is_favorite": False,
                    }
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
        404: {
            "description": "Вакансия с указанным ID не найдена.",
            "content": {
                "application/json": {
                    "example": {"detail": "Vacancy with id '12345' not found."}
                }
            },
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {
                "application/json": {
                    "example": {"detail": "A database error occurred while processing vacancies data."}
                }
            },
        },
    },
    response_model=VacancySchema,
)
async def get_vacancy_by_id(
    vacancy_id: Annotated[str, Path(description="ID вакансии")],
    vacancies_service: VacanciesServiceDep,
    user_id: Annotated[Optional[str], Query(description="Идентификатор пользователя во внешней системе")] = None,
):
    """Возвращает подробную информацию о вакансии по её ID.

    Args:
        vacancy_id: Уникальный идентификатор вакансии.
        vacancies_service: Сервис для работы с вакансиями.
        user_id: Идентификатор пользователя во внешней системе, опциональное поле.

    Returns:
        Модель с детальной информацией о вакансии.
    """
    logger.info("🚀 Запрос GET /{vacancy_id}. ID вакансии: %s.", vacancy_id)
    try:
        vacancy = await vacancies_service.get_vacancy_details(
            vacancy_id=vacancy_id, user_id=user_id
        )
        logger.info("✅ Запрос GET /{vacancy_id} выполнен. ID вакансии: %s.", vacancy_id)
        return vacancy
    except (
        VacanciesRepositoryError,
        FavoritesRepositoryError,
        VacancyNotFoundError,
        VacanciesServiceError,
        VacancyParseError,
        HHAPIRequestError,
        TVAPIRequestError,
    ) as error:
        logger.exception(
            "❌ Ошибка при получении вакансии. ID: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)
