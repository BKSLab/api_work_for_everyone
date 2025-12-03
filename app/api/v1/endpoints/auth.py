import logging

from fastapi import APIRouter, HTTPException, Request, status

from core.limiter import limiter
from dependencies.jwt import (
    CurrentUserPayloadDep,
    JWTManagerDep,
    get_current_refresh_payload,
)
from dependencies.services import BlocklistServiceDep, UsersServiceDep
from exceptions.jwt_exceptions import JWTManagerError
from exceptions.repository_exceptions import UsersRepositoryError
from exceptions.users_service_exceptions import (
    BlocklistServiceError,
    EmailNotVerifiedError,
    ExpiredCodeError,
    InvalidCodeError,
    InvalidCredentialsError,
    UserAlreadyExists,
    UserAlreadyVerified,
    UserInactiveError,
    UserNotFound,
    UsersServiceError,
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
    description=(
        """
        Регистрация нового пользователя по электронной почте.

        - Принимает `username`, `email`, `password`.
        - Сохраняет пользователя в базе данных с флагом `is_verified=False`.
        - Отправляет на указанный `email` письмо с кодом подтверждения.
        - Применяет ограничение скорости: не более 5 запросов в час.

        Возможные ошибки:
        - `409 Conflict`: Если пользователь с указанным email уже зарегистрирован.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса, например, если не удалось отправить код верификации.
        """
    ),
    response_model=MsgSchema,
)
@limiter.limit("5/hour")
async def user_register(
    request: Request,
    data: UserRegisterSchema,
    users_service: UsersServiceDep
):
    """Регистрирует нового пользователя и отправляет код верификации."""
    logger.info("Вызов обработчика /register.")
    try:
        await users_service.register_user_handler(user_data=data)
    except (
        UserAlreadyExists,
        UsersRepositoryError,
        UsersServiceError,
    ) as error:
        logger.error(
            "Ошибка регистрации пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /register завершил свою работу успешно.")
    return MsgSchema(msg="User registered successfully. Check your email for verification code.")


@router.post(
    path='/resend-verification-code',
    status_code=status.HTTP_200_OK,
    summary="Повторная отправка кода верификации",
    description=(
        """
        # Повторная отправка кода верификации на электронную почту.
        Позволяет пользователю, который не получил или потерял код верификации, запросить его повторно.

        - Принимает `email` пользователя.
        - Проверяет, что пользователь существует и еще не верифицирован.
        - Удаляет старые коды верификации и генерирует новый.
        - Отправляет новый код на указанный `email`.
        - Применяет ограничение скорости: максимум 3 запроса в 1 час.

        Возможные ошибки:
        - `404 Not Found`: Если пользователь с указанным email не найден.
        - `409 Conflict`: Если пользователь с указанным email уже прошел верификацию.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса, например, если не удалось отправить код верификации.
        """
    ),
    response_model=MsgSchema,
)
@limiter.limit("3/hour")
async def resend_verification_code(
    request: Request,
    data: EmailOnlySchema,
    users_service: UsersServiceDep
):
    """Повторно отправляет код верификации."""
    logger.info("Вызов обработчика /resend-verification-code.")
    try:
        await users_service.resend_verification_code(email=data.email)
    except (
        UserAlreadyVerified,
        UserNotFound,
        EmailNotVerifiedError,
        UsersServiceError
    ) as error:
        logger.error(
            "Ошибка повторной отправки кода верификации для пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /resend-verification-code завершил свою работу успешно.")
    return MsgSchema(msg="Verification code re-sent successfully. Check your email.")


@router.post(
    path='/forgot-password',
    status_code=status.HTTP_200_OK,
    summary="Запрос на сброс пароля",
    description=(
        """
        # Запрос на сброс пароля.

        Инициирует процесс сброса пароля для **существующего и верифицированного** пользователя.

        - Принимает `email` пользователя.
        - Удаляет все предыдущие коды сброса пароля для данного пользователя.
        - Генерирует и отправляет новый код сброса на указанный `email`.
        - Применяет ограничение скорости: максимум 3 запроса в 1 час.

        Возможные ошибки:
        - `404 Not Found`: Если пользователь с указанным email не найден или его аккаунт не верифицирован.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса, например, если не удалось отправить код сброса.
        """
    ),
    response_model=MsgSchema,
)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequestSchema,
    users_service: UsersServiceDep
):
    """Запрашивает сброс пароля для пользователя."""
    logger.info("Вызов обработчика /forgot-password.")
    try:
        await users_service.forgot_password(email=data.email)
    except (
        UserNotFound,
        UsersServiceError
    ) as error:
        logger.error(
            "Ошибка отправки кода сброса пароля для пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /forgot-password завершил свою работу успешно.")
    return MsgSchema(msg="Password reset code sent to your email.")


@router.post(
    path='/reset-password',
    status_code=status.HTTP_200_OK,
    summary="Сброс пароля",
    description=(
        """
        # Сброс пароля пользователя.

        Подтверждает код сброса пароля и устанавливает новый пароль для **верифицированного** пользователя.

        - Принимает `email`, `code` сброса и `new_password`.
        - Проверяет код сброса и устанавливает новый пароль в базе данных.
        - Удаляет использованный код сброса пароля.
        - Применяет ограничение скорости: максимум 5 попыток в 15 минут.

        Возможные ошибки:
        - `404 Not Found`: Если пользователь с указанным email не найден.
        - `403 Forbidden`: Если аккаунт пользователя не верифицирован.
        - `400 Bad Request`: Если код сброса недействителен или истек.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса.
        """
    ),
    response_model=MsgSchema,
)
@limiter.limit("5/15minute")
async def reset_password(
    request: Request,
    data: ResetPasswordRequestSchema,
    users_service: UsersServiceDep
):
    """Сбрасывает пароль пользователя с использованием кода."""
    logger.info("Вызов обработчика /reset-password.")
    try:
        await users_service.reset_password(user_data=data)
    except (
        UserNotFound,
        InvalidCodeError,
        ExpiredCodeError,
        EmailNotVerifiedError,
        UsersServiceError
    ) as error:
        logger.error(
            "Ошибка сброса пароля для пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /reset-password завершил свою работу успешно.")
    return MsgSchema(msg="Password has been reset successfully.")


@router.post(
    path='/verify-email',
    status_code=status.HTTP_200_OK,
    summary="Подтверждение адреса электронной почты",
    description=(
        """
        # Подтверждение адреса электронной почты пользователя.
        
        - Принимает `email` и `code` верификации.
        - При успехе, устанавливает флаг `is_verified=True` для пользователя.
        - Возвращает новую пару `access` и `refresh` токенов.
        - Применяет ограничение скорости: не более 10 запросов в час.

        Возможные ошибки:
        - `404 Not Found`: Если пользователь с указанным email не найден.
        - `409 Conflict`: Если пользователь с указанным email уже прошел верификацию.
        - `400 Bad Request`: Если код верификации недействителен или истек.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса.
        """
    ),
    response_model=TokenResponseSchema,
)
@limiter.limit("10/hour")
async def user_verify_email(
    request: Request,
    data: EmailVerifySchema,
    users_service: UsersServiceDep,
    jwt_manager: JWTManagerDep
):
    """Проверяет код верификации и активирует пользователя."""
    logger.info("Вызов обработчика /verify-email.")
    try:
        user = await users_service.verify_user_email(user_data=data)
        token_pair = await create_token_pair(
            jwt_manager=jwt_manager,
            user_email=user.email,
            username=user.username
        )
    except (
        UserNotFound,
        InvalidCodeError,
        ExpiredCodeError,
        UsersServiceError,
        JWTManagerError,
        UserAlreadyVerified
    ) as error:
        logger.error(
            "Ошибка активации почты для пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /verify-email завершил свою работу успешно.")
    return token_pair


@router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="Аутентификация пользователя",
    description=(
        """
        # Аутентификация пользователя по email и паролю.
        - Принимает `email` и `password`.
        - Проверяет учетные данные, статус верификации и активности пользователя.
        - При успехе, возвращает новую пару `access` и `refresh` токенов.
        - Применяет ограничение скорости: не более 5 попыток в 15 минут.

        Возможные ошибки:
        - `404 Not Found`: Если пользователь с указанным email не найден.
        - `403 Forbidden`: Если email пользователя не подтвержден или учетная запись не активна.
        - `401 Unauthorized`: Если предоставленные учетные данные (email/пароль) неверны.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса.
        """
    ),
    response_model=TokenResponseSchema,
)
@limiter.limit("5/15minute")
async def user_login(
    request: Request,
    data: UserLoginSchema,
    users_service: UsersServiceDep,
    jwt_manager: JWTManagerDep
):
    """Аутентифицирует пользователя и возвращает пару токенов."""
    logger.info("Вызов обработчика /login.")
    try:
        user = await users_service.login_user(user_data=data)
        token_pair = await create_token_pair(
            jwt_manager=jwt_manager,
            user_email=user.email,
            username=user.username
        )
    except (
        UsersRepositoryError,
        UserNotFound,
        EmailNotVerifiedError,
        UserInactiveError,
        InvalidCredentialsError
    ) as error:
        logger.error(
            "Ошибка актентифкации пользователя с email %s: %s",
            data.email,
            error,
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /login завершил свою работу успешно.")
    return token_pair


@router.post(
    path="/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход пользователя из системы",
    description=(
        """
        # Выход пользователя из системы (Stateful).

        - Принимает `access` токен в заголовке `Authorization: Bearer`
        - Добавляет идентификатор токена (`jti`) в черный список.
        - Последующие запросы с этим токеном будут отклонены.

        Возможные ошибки:
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса, например, если не удалось добавить токен в черный список.
        """
    ),
)
async def user_logout(
    payload: CurrentUserPayloadDep,
    blocklist_service: BlocklistServiceDep
):
    """Добавляет access токен в черный список для выхода из системы."""
    logger.info("Вызов обработчика /logout.")
    try:
        await blocklist_service.block_token(payload=payload)
        logger.info("Обрабочик /logout завершил свою работу успешно.")
    except BlocklistServiceError as error:
        logger.error(
            "Ошибка при добавлении токена в черный список: %s", error
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )


@router.post(
    path='/refresh',
    status_code=status.HTTP_200_OK,
    summary="Обновление пары токенов",
    description=(
        """
        # Обновление пары токенов с помощью refresh токена.

        - Принимает `refresh_token` в теле запроса.
        - Проверяет валидность и отсутствие `refresh_token` в черном списке.
        - Использованный `refresh_token` добавляется в черный список (ротация).
        - Возвращает новую пару `access` и `refresh` токенов.
        - Применяет ограничение скорости: не более 30 запросов в час.

        Возможные ошибки:
        - `401 Unauthorized`: Если refresh токен невалиден, просрочен или заблокирован.
        - `429 Too Many Requests`: При превышении лимита запросов.
        - `500 Internal Server Error`: В случае внутренних ошибок сервиса.
        """
    ),
    response_model=TokenResponseSchema,
)
@limiter.limit("30/hour")
async def refresh_token(
    request: Request,
    data: RefreshTokenRequestSchema,
    blocklist_service: BlocklistServiceDep,
    jwt_manager: JWTManagerDep
):
    """Обновляет access и refresh токены, блокируя использованный refresh токен."""
    logger.info("Вызов обработчика /refresh.")
    try:
        refresh_payload = await get_current_refresh_payload(
            data=data,
            jwt_manager=jwt_manager,
            blocklist_service=blocklist_service
        )
        # Блокируем использованный refresh токен
        await blocklist_service.block_token(payload=refresh_payload)

        token_pair = await create_token_pair(
            jwt_manager=jwt_manager,
            user_email=refresh_payload["sub"],
            username=refresh_payload["username"]
        )

    except (JWTManagerError, BlocklistServiceError) as error:
        logger.error(
            "Ошибка обновления токенов для пользователя: %s", error
        )
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail()
        )
    logger.info("Обрабочик /refresh завершил свою работу успешно.")
    return token_pair
