import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pprint import pformat
from typing import Any

import jwt

from core.settings import get_settings
from exceptions.jwt_manager import JWTManagerError

settings = get_settings()

logger = logging.getLogger(__name__)


# класс переработан
class JWTManager:
    """Класс для работы с токенами."""

    def __init__(
        self,
        private_key: str,
        public_key: str,
        algorithm: str,
        expires_in: int,
        refresh_expires_in_days: int
) -> None:
        self.private_key = private_key
        self.public_key = public_key
        self.algorithm = algorithm
        self.expires_in = expires_in
        self.refresh_expires_in_days = refresh_expires_in_days


    @classmethod
    def from_settings(cls) -> "JWTManager":
        """
        Фабричный метод для создания экземпляра JWTManager из настроек приложения.
        Сам класс не зависит от путей к ключам — только этот метод делает загрузку.
        """
        settings = get_settings()

        # фабрика знает про файлы, а сам класс — нет
        private_key = Path(settings.app.jwt_private_key_path).read_text()
        public_key = Path(settings.app.jwt_public_key_path).read_text()
        algorithm = settings.app.base_algoritm.get_secret_value()
        expires_in = settings.app.jwt_expire_seconds
        refresh_expires_in_days = settings.app.jwt_refresh_expire_days

        return cls(
            private_key=private_key,
            public_key=public_key,
            algorithm=algorithm,
            expires_in=expires_in,
            refresh_expires_in_days=refresh_expires_in_days
        )
    
    def create_access_token(self, payload: dict[str, Any]) -> str:
        """Создает access JWT токен."""
        now = datetime.now(timezone.utc)
        payload = {
            **payload,
            "exp": now + timedelta(seconds=self.expires_in),
            "iat": now,
            "type": "access",
            "jti": str(uuid.uuid4())
        }

        try:
            token = jwt.encode(
                payload=payload,
                key=self.private_key,
                algorithm=self.algorithm
            )
            logger.debug(
                "Access токен успешно создан. Пользователь: %s, истекает в %s",
                payload.get("user_id", "N/A"),
                payload["exp"],
            )
            return token

        except Exception as error:
            raise JWTManagerError(
                error_details=f"payload for token creation:\n{pformat(payload)}",
                message="Failed to create access token and refresh token"
            ) from error

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """Декодирует и проверяет access JWT токен."""
        try:
            decoded = jwt.decode(
                token,
                key=self.public_key,
                algorithms=[self.algorithm],
                options={"require": ["exp", "iat", "type", "jti"]},
            )

            if decoded.get("type") != "access":
                raise JWTManagerError(
                    error_details=f"token data: {token}",
                    message="Invalid token type: expected access token"
                )
    
            exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
            logger.debug(
                "Access токен успешно декодирован. Пользователь: %s, истекает в %s",
                decoded.get("user_id", "N/A"),
                exp.isoformat(),
            )
            return decoded

        except jwt.ExpiredSignatureError as error:
            logger.warning("Попытка использовать просроченный access токен.")
            raise JWTManagerError(
                error_details=f"token data: {token}",
                message="The access token has expired."
            ) from error

        except jwt.InvalidTokenError as error:
            logger.warning("Некорректный access токен: %s", e)
            raise JWTManagerError(
                error_details=f"token data: {token}",
                message="An invalid access token was passed.."
            ) from error

    def create_refresh_token(self, payload: dict[str, Any]) -> str:
        """Создает refresh JWT токен."""
        now = datetime.now(timezone.utc)
        refresh_payload = {
            **payload,
            "exp": now + timedelta(days=self.refresh_expires_in_days),
            "iat": now,
            "type": "refresh",
            "jti": str(uuid.uuid4())
        }
        try:
            token = jwt.encode(refresh_payload, self.private_key, algorithm=self.algorithm)
            logger.debug(
                "Refresh токен успешно создан. Пользователь: %s, истекает в %s",
                payload.get("user_id", "N/A"),
                refresh_payload["exp"],
            )
            return token
        except Exception as error:
            raise JWTManagerError(
                error_details=f"refresh_payload data:\n{pformat(refresh_payload)}",
                message="Error creating refresh token."
            ) from error

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """Декодирует и проверяет refresh JWT токен."""
        try:
            decoded = jwt.decode(
                token,
                key=self.public_key,
                algorithms=[self.algorithm],
                options={"require": ["exp", "iat", "type", "jti"]},
            )

            if decoded["type"] != "refresh":
                raise JWTManagerError(
                    error_details=f"token data: {token}",
                    message="Invalid token type: expected refresh token"
                )

            exp = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
            logger.debug(
                "Refresh токен успешно декодирован. Пользователь: %s, истекает в %s",
                decoded.get("user_id", "N/A"),
                exp.isoformat(),
            )
            return decoded

        except jwt.ExpiredSignatureError as error:
            raise JWTManagerError(
                error_details=f"token data: {token}",
                message="The refresh token has expired."
            ) from error
        except jwt.InvalidTokenError as error:
            raise JWTManagerError(
                error_details=f"token data: {token}",
                message="Invalid refresh token."
            ) from error
