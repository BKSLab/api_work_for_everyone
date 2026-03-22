import logging
from typing import Annotated, Optional

from fastapi import APIRouter, HTTPException, Path, Query, status

from dependencies.services import VacanciesServiceDep
from exceptions.api_clients import HHAPIRequestError, TVAPIRequestError
from exceptions.parsing_vacancies import VacancyParseError
from exceptions.repositories import (
    FavoritesRepositoryError,
    VacanciesRepositoryError,
)
from exceptions.services import VacanciesServiceError
from exceptions.vacancies import VacancyAlreadyInFavoritesError, VacancyNotFoundError
from schemas.vacancies import (
    FavoriteVacanciesListSchema,
    MsgSchema,
    VacancyAddFavoriteSchema,
    VacancySchema,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    path="/add-vacancy",
    status_code=status.HTTP_201_CREATED,
    summary="Добавление вакансии в избранное",
    description="Добавляет вакансию в избранное для зарегистрированного пользователя.",
    operation_id="addVacancyToFavorites",
    response_description="Сообщение об успешном добавлении вакансии в избранное",
    responses={
        201: {
            "description": "Вакансия успешно добавлена в избранное.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "The vacancy with vacancy_id=12345 has been successfully added to your favorites."
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
            "description": "Вакансия не найдена.",
            "content": {
                "application/json": {
                    "example": {"detail": "Vacancy with id '12345' not found."}
                }
            },
        },
        409: {
            "description": "Вакансия уже добавлена в избранное.",
            "content": {
                "application/json": {
                    "example": {"detail": "Vacancy is already in favorites."}
                }
            },
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {
                "application/json": {
                    "example": {"detail": "A database error occurred while processing favorites data."}
                }
            },
        },
    },
    response_model=MsgSchema,
)
async def add_vacancy(
    data: VacancyAddFavoriteSchema,
    vacancies_service: VacanciesServiceDep,
):
    """Добавляет вакансию в избранное для текущего пользователя.

    Args:
        data: Данные для добавления вакансии в избранное.
        vacancies_service: Сервис для работы с вакансиями.

    Returns:
        Сообщение об успешном добавлении вакансии.
    """
    user_id = data.user_id
    vacancy_id = data.vacancy_id
    logger.info(
        "🚀 Запрос POST /add-vacancy. Пользователь: '%s', вакансия: %s.",
        user_id,
        vacancy_id,
    )
    try:
        await vacancies_service.add_vacancy_to_favorites(
            vacancy_id=vacancy_id, user_id=user_id
        )
    except (
        VacanciesRepositoryError,
        VacancyNotFoundError,
        VacanciesServiceError,
        FavoritesRepositoryError,
        VacancyAlreadyInFavoritesError

    ) as error:
        logger.exception(
            "❌ Ошибка при добавлении вакансии в избранное. ID вакансии: %s, ID пользователя: %s. Детали: %s",
            vacancy_id,
            user_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)

    logger.info(
        "✅ Запрос POST /add-vacancy выполнен. Пользователь: '%s', вакансия: %s.",
        user_id,
        vacancy_id,
    )
    return MsgSchema(
        message=f"Вакансия с vacancy_id={data.vacancy_id} успешно добавлена в избранное."
    )


@router.post(
    path="/delete-vacancy",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление вакансии из избранного",
    description="Удаляет вакансию из избранного для зарегистрированного пользователя.",
    operation_id="deleteVacancyFromFavorites",
    response_description="Вакансия успешно удалена, тело ответа отсутствует",
    responses={
        204: {"description": "Вакансия успешно удалена из избранного."},
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
            "description": "Вакансия не найдена в избранном.",
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
                    "example": {"detail": "A database error occurred while processing favorites data."}
                }
            },
        },
    },
)
async def delete_vacancy(
    data: VacancyAddFavoriteSchema,
    vacancies_service: VacanciesServiceDep,
):
    """Удаляет вакансию из избранного для текущего пользователя.

    Args:
        data: Данные для удаления вакансии из избранного.
        vacancies_service: Сервис для работы с вакансиями.
    """
    user_id = data.user_id
    vacancy_id = data.vacancy_id
    logger.info(
        "🚀 Запрос POST /delete-vacancy. Пользователь: '%s', вакансия: %s.",
        user_id,
        vacancy_id,
    )
    try:
        await vacancies_service.delete_vacancy_from_favorites(
            vacancy_id=vacancy_id, user_id=user_id
        )
        logger.info(
            "✅ Запрос POST /delete-vacancy выполнен. Пользователь: '%s', вакансия: %s.",
            user_id,
            vacancy_id,
        )
        return
    except (
        VacancyNotFoundError,
        FavoritesRepositoryError
    ) as error:
        logger.exception(
            "❌ Ошибка при удалении вакансии из избранного. ID вакансии: %s, ID пользователя: %s. Детали: %s",
            vacancy_id,
            user_id,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail
        )


@router.get(
    path="/list",
    status_code=status.HTTP_200_OK,
    summary="Получение списка избранных вакансий с пагинацией",
    description="Возвращает список вакансий, добавленных пользователем в избранное, с поддержкой пагинации.",
    operation_id="getFavoritesVacancies",
    response_description="Список избранных вакансий с информацией о пагинации",
    responses={
        200: {
            "description": "Список избранных вакансий успешно получен.",
            "content": {
                "application/json": {
                    "example": {
                        "total": 25,
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
                                "is_favorite": True,
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
                    "example": {"detail": "A database error occurred while processing favorites data."}
                }
            },
        },
    },
    response_model=FavoriteVacanciesListSchema,
)
async def get_favorites_vacancies(
    vacancies_service: VacanciesServiceDep,
    user_id: Annotated[
        str, Query(
            description='Идентификатор пользователя.'
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
    """Возвращает список избранных вакансий пользователя с пагинацией.

    Args:
        vacancies_service: Сервис для работы с вакансиями.
        user_id: Идентификатор пользователя.
        page: Номер страницы для пагинации.
        page_size: Количество вакансий на странице.

    Returns:
        Список избранных вакансий с информацией о пагинации.
    """
    logger.info(
        "🚀 Запрос GET /favorites/list. Пользователь: '%s', страница: %s, размер: %s.",
        user_id,
        page,
        page_size,
    )
    try:
        favorites_data = await vacancies_service.get_user_favorites(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        logger.info("✅ Запрос GET /favorites/list выполнен. Пользователь: '%s'.", user_id)
        return favorites_data
    except (
        HHAPIRequestError,
        TVAPIRequestError,
        VacanciesRepositoryError,
        VacanciesServiceError,
    ) as error:
        logger.exception(
            "❌ Ошибка при получении избранных вакансий. ID пользователя: %s. Детали: %s",
            user_id,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail
        )


@router.get(
    path="/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Получение детальной информации о вакансии из избранного",
    description="Возвращает подробную информацию о конкретной вакансии по её ID.",
    operation_id="getFavoriteVacancyById",
    response_description="Детальная информация о вакансии из избранного",
    responses={
        200: {
            "description": "Детальная информация о вакансии из избранного успешно получена.",
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
            "description": "Вакансия с указанным ID не найдена в избранном.",
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
async def get_favorites_vacancy_by_id(
    vacancy_id: Annotated[str, Path(description="ID вакансии")],
    vacancies_service: VacanciesServiceDep,
    user_id: Annotated[str, Query(description="Идентификатор пользователя во внешней системе")] = None,
):
    """Возвращает подробную информацию о вакансии из избранного по её ID.

    Args:
        vacancy_id: Уникальный идентификатор вакансии.
        vacancies_service: Сервис для работы с вакансиями.
        user_id: Идентификатор пользователя во внешней системе, опциональное поле.

    Returns:
        Модель с детальной информацией о вакансии.
    """
    logger.info("🚀 Запрос GET /favorites/{vacancy_id}. ID вакансии: %s.", vacancy_id)
    try:
        vacancy = await vacancies_service.get_vacancy_by_id_from_favorites(
            vacancy_id=vacancy_id, user_id=user_id
        )
        logger.info("✅ Запрос GET /favorites/{vacancy_id} выполнен. ID вакансии: %s.", vacancy_id)
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
