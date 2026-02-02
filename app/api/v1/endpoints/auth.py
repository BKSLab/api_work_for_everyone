import logging

from fastapi import APIRouter, HTTPException, Request, status

from core.limiter import limiter
from dependencies.jwt import (
    CurrentUserPayloadDep,
    JWTManagerDep,
    get_current_refresh_payload,
)
from dependencies.services import BlocklistServiceDep, UsersServiceDep
from exceptions.jwt_manager import JWTManagerError
from exceptions.repositories import BlocklistRepositoryError, UsersRepositoryError
from exceptions.services import BlocklistServiceError, UsersServiceError
from exceptions.users import (
    EmailNotVerifiedError,
    ExpiredCodeError,
    InvalidCodeError,
    InvalidCredentialsError,
    SendOtpCodeError,
    UserAlreadyExists,
    UserAlreadyVerified,
    UserInactiveError,
    UserNotFound,
)
from schemas.users import (
    EmailOnlySchema,
    EmailVerifySchema,
    ForgotPasswordRequestSchema,
    MsgSchema,
    RefreshTokenRequestSchema,
    ResetPasswordRequestSchema,
    TokenResponseSchema,
    UserLoginSchema,
    UserRegisterSchema,
)
from utils.create_token import create_token_pair

router = APIRouter()
logger = logging.getLogger(__name__)



@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Регистрирует нового пользователя, отправляя код подтверждения на email.",
    responses={
        201: {
            "description": "Пользователь успешно зарегистрирован, код подтверждения отправлен."
        },
        409: {"description": "Пользователь с таким email уже существует."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=MsgSchema,
)
@limiter.limit("5/hour")
async def user_register(
    request: Request, data: UserRegisterSchema, users_service: UsersServiceDep
):
    """Регистрирует нового пользователя и отправляет код верификации.

    - Сохраняет пользователя в базе данных с флагом `is_verified=False`.
    - Отправляет на указанный `email` письмо с кодом подтверждения.

    Args:
        request: Объект запроса FastAPI.
        data: Данные для регистрации пользователя (username, email, password).
        users_service: Сервис для работы с пользователями.

    Returns:
        Сообщение об успешной регистрации.
    """
    logger.info("Начало обработки /register для пользователя с email %s.", data.email)
    try:
        await users_service.register_user_handler(user_data=data)
        logger.info(
            "Успешное завершение /register для пользователя с email %s.", data.email
        )
        return MsgSchema(
            msg="User registered successfully. Check your email for verification code."
        )
    except (
        UsersRepositoryError,
        UserAlreadyExists,
        UsersServiceError,
        SendOtpCodeError,
    ) as error:
        logger.exception(
            "Ошибка регистрации пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/resend-verification-code",
    status_code=status.HTTP_200_OK,
    summary="Повторная отправка кода верификации",
    description="Повторно отправляет код верификации на email пользователя.",
    responses={
        200: {"description": "Код верификации успешно отправлен повторно."},
        404: {"description": "Пользователь с указанным email не найден."},
        409: {"description": "Пользователь уже прошел верификацию."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=MsgSchema,
)
@limiter.limit("3/hour")
async def resend_verification_code(
    request: Request, data: EmailOnlySchema, users_service: UsersServiceDep
):
    """Повторно отправляет код верификации.

    - Проверяет, что пользователь существует и еще не верифицирован.
    - Генерирует и отправляет новый код на указанный `email`.

    Args:
        request: Объект запроса FastAPI.
        data: Email пользователя.
        users_service: Сервис для работы с пользователями.

    Returns:
        Сообщение об успешной отправке кода.
    """
    logger.info("Начало обработки /resend-verification-code для %s.", data.email)
    try:
        await users_service.resend_verification_code(email=data.email)
        logger.info("Успешное завершение /resend-verification-code для %s.", data.email)
        return MsgSchema(
            msg="Verification code re-sent successfully. Check your email."
        )
    except (
        UsersRepositoryError,
        UserNotFound,
        UserAlreadyVerified,
        SendOtpCodeError,
    ) as error:
        logger.exception(
            "Ошибка при повторной отправке кода для %s: %s",
            data.email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Запрос на сброс пароля",
    description="Инициирует сброс пароля, отправляя код на email пользователя.",
    responses={
        200: {"description": "Код сброса пароля успешно отправлен."},
        404: {"description": "Пользователь не найден или не верифицирован."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=MsgSchema,
)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request, data: ForgotPasswordRequestSchema, users_service: UsersServiceDep
):
    """Запрашивает сброс пароля для пользователя.

    - Генерирует и отправляет код сброса на `email` верифицированного пользователя.

    Args:
        request: Объект запроса FastAPI.
        data: Email пользователя.
        users_service: Сервис для работы с пользователями.

    Returns:
        Сообщение об успешной отправке кода.
    """
    logger.info("Начало обработки /forgot-password для %s.", data.email)
    try:
        await users_service.forgot_password(email=data.email)
        logger.info("Успешное завершение /forgot-password для %s.", data.email)
        return MsgSchema(msg="Password reset code sent to your email.")
    except (UsersRepositoryError, UserNotFound, SendOtpCodeError, UsersServiceError) as error:
        logger.exception(
            "Ошибка отправки кода сброса пароля для пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Сброс пароля",
    description="Устанавливает новый пароль для пользователя с использованием кода сброса.",
    responses={
        200: {"description": "Пароль успешно сброшен."},
        400: {"description": "Неверный или просроченный код сброса."},
        403: {"description": "Аккаунт пользователя не верифицирован."},
        404: {"description": "Пользователь с указанным email не найден."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=MsgSchema,
)
@limiter.limit("5/15minute")
async def reset_password(
    request: Request, data: ResetPasswordRequestSchema, users_service: UsersServiceDep
):
    """Сбрасывает пароль пользователя с использованием кода.

    - Проверяет код сброса и устанавливает новый пароль.

    Args:
        request: Объект запроса FastAPI.
        data: Данные для сброса пароля (email, код, новый пароль).
        users_service: Сервис для работы с пользователями.

    Returns:
        Сообщение об успешном сбросе пароля.
    """
    logger.info("Начало обработки /reset-password для %s.", data.email)
    try:
        await users_service.reset_password(user_data=data)
        logger.info("Успешное завершение /reset-password для %s.", data.email)
        return MsgSchema(msg="Password has been reset successfully.")
    except (
        UsersRepositoryError,
        UserNotFound,
        InvalidCodeError,
        ExpiredCodeError,
        EmailNotVerifiedError,
        UsersServiceError,
    ) as error:
        logger.exception(
            "Ошибка сброса пароля для %s: %s",
            data.email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/verify-email",
    status_code=status.HTTP_200_OK,
    summary="Подтверждение адреса электронной почты",
    description="Подтверждает email пользователя с помощью кода верификации и возвращает токены.",
    responses={
        200: {"description": "Email успешно подтвержден, возвращена пара токенов."},
        400: {"description": "Неверный или просроченный код верификации."},
        401: {"description": "Ошибка при создании пары токенов."},
        404: {"description": "Пользователь с таким email не найден."},
        409: {"description": "Пользователь уже прошел верификацию."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=TokenResponseSchema,
)
@limiter.limit("10/hour")
async def user_verify_email(
    request: Request,
    data: EmailVerifySchema,
    users_service: UsersServiceDep,
    jwt_manager: JWTManagerDep,
):
    """Проверяет код верификации, активирует пользователя и возвращает пару токенов.

    Args:
        request: Объект запроса FastAPI.
        data: Данные для верификации (email, код).
        users_service: Сервис для работы с пользователями.
        jwt_manager: Менеджер для работы с JWT.

    Returns:
        Новая пара access и refresh токенов.
    """
    logger.info("Начало обработки /verify-email для %s.", data.email)
    try:
        # Проверка кода верификации и получение данных пользователя
        user = await users_service.verify_user_email(user_data=data)

        # Создание токенов для пользователя
        token_pair = await create_token_pair(
            jwt_manager=jwt_manager, user_email=user.email, username=user.username
        )

        logger.info("Успешное завершение /verify-email для %s.", data.email)
        return token_pair
    except (
        UserNotFound,
        UserAlreadyVerified,
        UsersRepositoryError,
        InvalidCodeError,
        ExpiredCodeError,
        JWTManagerError,
    ) as error:
        logger.exception(
            "Ошибка верификации почты для %s: %s",
            data.email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="Аутентификация пользователя",
    description="Аутентифицирует пользователя и возвращает пару access и refresh токенов.",
    responses={
        200: {"description": "Аутентификация прошла успешно, возвращена пара токенов."},
        401: {"description": "Неверные учетные данные или ошибка создания токенов."},
        403: {"description": "Email не подтвержден или аккаунт неактивен."},
        404: {"description": "Пользователь с таким email не найден."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=TokenResponseSchema,
)
@limiter.limit("5/15minute")
async def user_login(
    request: Request,
    data: UserLoginSchema,
    users_service: UsersServiceDep,
    jwt_manager: JWTManagerDep,
):
    """Аутентифицирует пользователя и возвращает пару токенов.

    - Проверяет учетные данные, статус верификации и активности пользователя.
    - При успехе возвращает новую пару `access` и `refresh` токенов.

    Args:
        request: Объект запроса FastAPI.
        data: Данные для входа (email, пароль).
        users_service: Сервис для работы с пользователями.
        jwt_manager: Менеджер для работы с JWT.

    Returns:
        Новая пара access и refresh токенов.
    """
    logger.info("Начало обработки /login для %s.", data.email)
    try:
        user = await users_service.login_user(user_data=data)
        token_pair = await create_token_pair(
            jwt_manager=jwt_manager, user_email=user.email, username=user.username
        )
        logger.info("Успешное завершение /login для %s.", data.email)
        return token_pair
    except (
        UsersRepositoryError,
        UserNotFound,
        EmailNotVerifiedError,
        UserInactiveError,
        InvalidCredentialsError,
        JWTManagerError,
    ) as error:
        logger.exception(
            "Ошибка аутентификации для %s: %s",
            data.email,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход пользователя из системы",
    description="Выход пользователя из системы путем добавления текущего access токена в черный список.",
    responses={
        204: {"description": "Токен успешно добавлен в черный список, выход выполнен."},
        401: {"description": "Неавторизованный доступ."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
)
async def user_logout(
    payload: CurrentUserPayloadDep, blocklist_service: BlocklistServiceDep
):
    """Добавляет access токен в черный список для выхода из системы.

    Args:
        payload: Данные JWT-токена текущего пользователя.
        blocklist_service: Сервис для работы с черным списком токенов.
    """
    email = payload.get("sub")
    logger.info("Начало обработки /logout для %s.", email)
    try:
        await blocklist_service.block_token(payload=payload)
        logger.info("Успешное завершение /logout для %s.", email)
    except (BlocklistServiceError, BlocklistRepositoryError) as error:
        logger.exception(
            "Ошибка при добавлении токена в черный список для %s: %s", email, error
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    summary="Обновление пары токенов",
    description="Обновляет пару токенов, используя refresh токен.",
    responses={
        200: {"description": "Пара токенов успешно обновлена."},
        401: {"description": "Refresh токен невалиден, просрочен или заблокирован."},
        429: {"description": "Превышен лимит запросов."},
        500: {"description": "Внутренняя ошибка сервиса."},
    },
    response_model=TokenResponseSchema,
)
@limiter.limit("30/hour")
async def refresh_token(
    request: Request,
    data: RefreshTokenRequestSchema,
    blocklist_service: BlocklistServiceDep,
    jwt_manager: JWTManagerDep,
):
    """Обновляет access и refresh токены, блокируя использованный refresh токен.

    Args:
        request: Объект запроса FastAPI.
        data: Refresh токен.
        blocklist_service: Сервис для работы с черным списком токенов.
        jwt_manager: Менеджер для работы с JWT.

    Returns:
        Новая пара access и refresh токенов.
    """
    logger.info("Начало обработки /refresh.")
    try:
        refresh_payload = await get_current_refresh_payload(
            data=data, jwt_manager=jwt_manager, blocklist_service=blocklist_service
        )
        user_email = refresh_payload.get("sub")
        logger.info("Обновление токенов для пользователя %s.", user_email)

        # Блокируем использованный refresh токен
        await blocklist_service.block_token(payload=refresh_payload)

        # Создаем новую пару токенов
        token_pair = await create_token_pair(
            jwt_manager=jwt_manager,
            user_email=user_email,
            username=refresh_payload.get("username"),
        )

        logger.info("Успешное завершение /refresh для %s.", user_email)
        return token_pair
    except (BlocklistServiceError, BlocklistRepositoryError, JWTManagerError) as error:
        logger.exception("Ошибка обновления токенов: %s", error)
        raise HTTPException(status_code=error.status_code, detail=error.detail)
