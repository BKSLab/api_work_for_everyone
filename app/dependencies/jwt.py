import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

from dependencies.services import BlocklistServiceDep
from exceptions.jwt_manager import JWTManagerError
from schemas.users import RefreshTokenRequestSchema
from utils.jwt.manager import JWTManager

bearer_scheme = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_jwt_manager() -> JWTManager:
    """Возвращает синглтон экземпляра экземпляра JWTManager."""
    return JWTManager.from_settings()


JWTManagerDep = Annotated[JWTManager, Depends(get_jwt_manager)]


TokenDep = Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]


async def get_current_user_payload(
    credentials: TokenDep,
    jwt_manager: JWTManagerDep,
    blocklist_service: BlocklistServiceDep
) -> dict:
    """
    Извлекает, валидирует и декодирует access токен, возвращая его payload.

    Эта зависимость является "охранником" для защищенных эндпоинтов.

    Последовательность действий:
    1.  Проверяет наличие заголовка `Authorization: Bearer <token>`.
        *   Если заголовок отсутствует, выбрасывает `HTTP 401 Unauthorized`.
    2.  Вызывает `jwt_manager` для декодирования и валидации токена.
        `jwt_manager` проверяет:
        - Тип токена (`type` должен быть `access`).
        - Срок действия токена (`exp`).
        - Подпись токена.
        *   В случае любой ошибки валидации, выбрасывает `HTTP 401 Unauthorized`.
    3.  Проверяет, не находится ли токен в черном списке.
        *   Если токен заблокирован (logout), выбрасывает `HTTP 401 Unauthorized`.
    4.  При успехе возвращает `payload` токена.

    Возвращает:
    *   `dict`: `payload` успешно валидированного токена.

    Выбрасывает исключения:
    *   `HTTPException` (401): Если токен отсутствует, невалиден, просрочен или заблокирован.
    """
    if credentials is None:
        logger.warning("Попытка доступа без аутентификационных данных.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token = credentials.credentials
        payload = jwt_manager.decode_access_token(token)
        if await blocklist_service.is_token_blocked(payload):
            logger.warning(
                "Попытка доступа с заблокированным токеном (jti: %s)", payload.get("jti")
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(
            "Доступ разрешен для пользователя: %s", payload.get("sub")
        )
        return payload
    except JWTManagerError as error:
        logger.warning("Ошибка валидации токена: %s", error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_refresh_payload(
    data: RefreshTokenRequestSchema,
    jwt_manager: JWTManagerDep,
    blocklist_service: BlocklistServiceDep
) -> dict:
    """
    Декодирует, валидирует и проверяет refresh токен на наличие в черном списке,
    возвращая его payload.

    Последовательность действий:
    1.  Принимает `RefreshTokenRequestSchema`, гарантируя наличие `refresh_token`.
    2.  Вызывает `jwt_manager` для декодирования и валидации refresh токена.
        `jwt_manager` проверяет:
        - Тип токена (`type` должен быть `refresh`).
        - Срок действия токена (`exp`).
        - Подпись токена.
        *   В случае любой ошибки валидации, выбрасывает `HTTP 401 Unauthorized`.
    3.  Проверяет, не находится ли refresh токен в черном списке.
        *   Если токен заблокирован (например, после предыдущего обновления или явного logout),
            выбрасывает `HTTP 401 Unauthorized`.
    4.  При успехе возвращает `payload` токена.

    Возвращает:
    *   `dict`: `payload` успешно валидированного refresh токена.

    Выбрасывает исключения:
    *   `HTTPException` (401): Если токен невалиден, просрочен или заблокирован.
    """
    payload = jwt_manager.decode_refresh_token(data.refresh_token)
    if await blocklist_service.is_token_blocked(payload):
        logger.warning(
            "Попытка обновления с заблокированным refresh токеном (jti: %s)", payload.get("jti")
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(
        "Refresh токен успешно валидирован для пользователя: %s", payload.get("sub")
    )
    return payload


CurrentUserPayloadDep = Annotated[dict, Depends(get_current_user_payload)]
