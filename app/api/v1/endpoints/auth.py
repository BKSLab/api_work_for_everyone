from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from dependencies.services import UsersServiceDep
from schemas.users import (
    EmailVerifySchema, MsgSchema, TokenResponseSchema, UserLoginSchema, UserRegisterSchema
)


router = APIRouter()


@router.post(
    path='/register',
    summary=(
        'Регистрация нового пользователя по электронной почте.'
    ),
    description=(
        '# POST /auth/register -> Регистрация нового пользователя по электронной почте. '
        'Принимает `username`, `email`, `password`. Сохраняет пользователя, '
        'отправляет письмо с кодом/ссылкой подтверждения'
    ),
    response_model=MsgSchema
)
async def user_register(
    data: UserRegisterSchema,
    users_service: UsersServiceDep
):
    """
    Регистрация нового пользователя по электронной почте.
    """
    # TODO: 1. Проверить, существует ли пользователь с таким email или username.
    #       users_service.check_user_exists должен выбрасывать HTTPException(409) если пользователь найден.
    await users_service.check_user_exists(
        email=data.email,
        username=data.username
    )

    # TODO: 2. Создать пользователя в базе данных со статусом is_verified=False.
    #       Этот метод должен быть в users_service и включать хеширование пароля.
    #       Например: await users_service.create_user(data)

    # TODO: 3. Сгенерировать и отправить код подтверждения на email.
    #       Логику отправки лучше вынести в отдельный email_service.
    #       Например: await email_service.send_verification_code(data.email)

    # TODO: 4. Вернуть успешный ответ.
    return MsgSchema(msg="User registered. Check your email for verification code.")


@router.post(
    path='/verify-email',
    summary=(
        'Подтверждение адреса электронной почты'
    ),
    description=(
        '# POST /auth/verify-email -> Подтверждение адреса электронной почты. '
        'Принимает `email` + `code` (или токен). Устанавливает флаг `is_verified=True`'
    ),
    response_model=TokenResponseSchema
)
async def user_verify_email(
    data: EmailVerifySchema,
    users_service: UsersServiceDep
):
    """
    Подтверждение адреса электронной почты.
    """
    return TokenResponseSchema(
        access_token="dummy_access_token", 
        refresh_token="dummy_refresh_token"
    )


@router.post(
    path='/login',
    summary=(
        'Аутентификация пользователя'
    ),
    description=(
        '# POST /auth/login -> Аутентификация пользователя. '
        'Принимает `email`, `password`. Проверяет хэш, '
        'выдает JWT (только если `is_verified=True`)'
    ),
    response_model=TokenResponseSchema
)
async def user_login(
    data: UserLoginSchema,
    users_service: UsersServiceDep
):
    """
    Аутентификация пользователя.
    """
    return TokenResponseSchema(
        access_token="dummy_access_token", 
        refresh_token="dummy_refresh_token"
    )


@router.post(
    path='/logout',
    summary=(
        'Выход пользователя из системы'
    ),
    description=(
        '# POST /auth/logout -> Выход пользователя из системы. '
        'В простом варианте просто удаляется токен на клиенте'
    ),
    response_model=MsgSchema
)
async def user_logout():
    """
    Выход пользователя из системы.
    """
    return MsgSchema(msg="User logged out.")
