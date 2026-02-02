import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from dependencies.jwt import CurrentUserPayloadDep
from dependencies.services import UsersServiceDep, VacanciesServiceDep
from exceptions.api_clients import HHAPIRequestError, TVAPIRequestError
from exceptions.repositories import (
    FavoritesRepositoryError,
    UsersRepositoryError,
    VacanciesRepositoryError,
)
from exceptions.services import VacanciesServiceError
from exceptions.users import UserNotFound
from exceptions.vacancies import VacancyAlreadyInFavoritesError, VacancyNotFoundError
from schemas.users import MsgSchema
from schemas.vacancies import FavoriteVacanciesListSchema, VacancyAddFavoriteSchema

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    path="/add-vacancy/{vacancy_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Добавление вакансии в избранное",
    description="Добавляет вакансию в избранное для зарегистрированного пользователя.",
    responses={
        201: {"description": "Вакансия успешно добавлена в избранное."},
        401: {"description": "Неавторизованный доступ."},
        404: {"description": "Пользователь или вакансия не найдены."},
        409: {"description": "Попытка повторно добавить вакансию пользователем в избранное."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    response_model=MsgSchema,
)
async def add_vacancy(
    data: VacancyAddFavoriteSchema,
    payload: CurrentUserPayloadDep,
    vacancies_service: VacanciesServiceDep,
    users_service: UsersServiceDep,
):
    """Добавляет вакансию в избранное для текущего пользователя.

    Args:
        data: Данные для добавления вакансии в избранное.
        payload: Данные JWT-токена текущего пользователя.
        vacancies_service: Сервис для работы с вакансиями.
        users_service: Сервис для работы с пользователями.

    Returns:
        Сообщение об успешном добавлении вакансии.
    """
    email = payload.get("sub")
    vacancy_id = data.vacancy_id
    logger.info(
        "Начало обработки /add-vacancy для '%s' (вакансия %s).",
        email,
        vacancy_id,
    )
    try:
        user_id = await users_service.get_user_data(email=email)

        await vacancies_service.add_vacancy_to_favorites(
            vacancy_id=vacancy_id, user_id=user_id
        )
    except (
        VacanciesRepositoryError,
        UsersRepositoryError,
        UserNotFound,
        VacancyNotFoundError,
        VacanciesServiceError,
        FavoritesRepositoryError,
        VacancyAlreadyInFavoritesError

    ) as error:
        logger.exception(
            "Ошибка при добавлении вакансии в избранное. vacancy_id: %s, email: %s, ошибка: %s",
            vacancy_id,
            email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)

    logger.info(
        "Успешное завершение /add-vacancy для '%s' (вакансия %s).",
        email,
        vacancy_id,
    )
    return MsgSchema(
        msg=f"The vacancy with vacancy_id={data.vacancy_id} has been successfully "
        "added to your favorites."
    )


@router.post(
    path="/delete-vacancy/{vacancy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление вакансии из избранного",
    description="Удаляет вакансию из избранного для зарегистрированного пользователя.",
    responses={
        204: {"description": "Вакансия успешно удалена из избранного."},
        401: {"description": "Неавторизованный доступ."},
        404: {"description": "Пользователь или вакансия не найдены."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
)
async def delete_vacancy(
    data: VacancyAddFavoriteSchema,
    payload: CurrentUserPayloadDep,
    vacancies_service: VacanciesServiceDep,
    users_service: UsersServiceDep,
):
    """Удаляет вакансию из избранного для текущего пользователя.

    Args:
        data: Данные для удаления вакансии из избранного.
        payload: Данные JWT-токена текущего пользователя.
        vacancies_service: Сервис для работы с вакансиями.
        users_service: Сервис для работы с пользователями.
    """
    email = payload.get("sub")
    vacancy_id = data.vacancy_id
    logger.info(
        "Начало обработки /delete-vacancy для '%s' (вакансия %s).",
        email,
        vacancy_id,
    )
    try:
        user_id = await users_service.get_user_data(email=email)

        await vacancies_service.delete_vacancy_from_favorites(
            vacancy_id=vacancy_id, user_id=user_id
        )
        logger.info(
            "Успешное завершение /delete-vacancy для '%s' (вакансия %s).",
            email,
            vacancy_id,
        )
        return
    except (
        UsersRepositoryError,
        UserNotFound,
        VacancyNotFoundError,
        FavoritesRepositoryError
    ) as error:
        logger.exception(
            "Ошибка при удалении вакансии из избранного. vacancy_id: %s, email: %s, ошибка: %s",
            vacancy_id,
            email,
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
    responses={
        200: {"description": "Список избранных вакансий успешно получен."},
        401: {"description": "Неавторизованный доступ."},
        404: {"description": "Пользователь не найден."},
        500: {"description": "Внутренняя ошибка сервера."},
    },
    response_model=FavoriteVacanciesListSchema,
)
async def get_favorites_vacancies(
    payload: CurrentUserPayloadDep,
    users_service: UsersServiceDep,
    vacancies_service: VacanciesServiceDep,
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
        payload: Данные JWT-токена текущего пользователя.
        users_service: Сервис для работы с пользователями.
        vacancies_service: Сервис для работы с вакансиями.
        page: Номер страницы для пагинации.
        page_size: Количество вакансий на странице.

    Returns:
        Список избранных вакансий с информацией о пагинации.
    """
    email = payload.get("sub")
    logger.info(
        "Начало обработки /list для '%s' (страница %s, размер %s).",
        email,
        page,
        page_size,
    )
    try:
        user_id = await users_service.get_user_data(email=email)
        favorites_data = await vacancies_service.get_user_favorites(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        logger.info("Успешное завершение /list для '%s'.", email)
        return favorites_data
    except (
        UsersRepositoryError,
        UserNotFound,
        HHAPIRequestError,
        TVAPIRequestError,
        VacanciesRepositoryError,
        VacanciesServiceError,
    ) as error:
        logger.exception(
            "Ошибка при получении избранных вакансий. email: %s, ошибка: %s",
            email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail
        )
