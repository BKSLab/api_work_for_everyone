import logging
from datetime import datetime, timezone

from core.settings import Settings
from db.models.api_keys import ApiKey
from exceptions.api_keys import (
    ApiKeyNotFoundError,
    ExpiredApiKeyError,
    InactiveApiKeyError,
    InvalidApiKeyError,
    MasterApiKeyError,
)
from repositories.api_keys import ApiKeyRepository
from schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyStatusResponse
from utils.security import (
    DB_PREFIX_SECRET_LENGTH,
    generate_api_key,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)


class ApiKeyService:
    """Сервис для валидации и создания API-ключей."""

    def __init__(
            self,
            api_key_repository: ApiKeyRepository,
            settings: Settings,
    ):
        self.api_key_repository = api_key_repository
        self.settings = settings

    async def validate_api_key(self, api_key: str) -> ApiKey:
        """
        Валидирует API-ключ, проверяя его по префиксу и сверяя с хешем в БД.
        """
        if "_" not in api_key:
            raise InvalidApiKeyError()

        parts = api_key.split("_")
        key_prefix = parts[0]
        secret_part = parts[1]

        # Восстанавливаем префикс, который хранится в БД
        db_prefix = f"{key_prefix}_{secret_part[:DB_PREFIX_SECRET_LENGTH]}"

        # Находим ключ по префиксу
        api_key_obj = await self.api_key_repository.get_by_prefix(db_prefix)

        # Если по префиксу ничего не найдено, или ключ не прошел проверку хеша
        if api_key_obj is None or not verify_password(
            plain_password=api_key, hashed_password=api_key_obj.hashed_key
        ):
            raise InvalidApiKeyError()

        if not api_key_obj.is_active:
            raise InactiveApiKeyError(api_key_prefix=db_prefix)

        if api_key_obj.expires_at is not None and api_key_obj.expires_at < datetime.now(
            timezone.utc
        ):
            raise ExpiredApiKeyError(api_key_prefix=db_prefix)

        return api_key_obj

    async def create_api_key(
            self,
            api_key_data: ApiKeyCreate,
            master_key: str,
    ) -> ApiKeyResponse:
        """
        Создает, сохраняет и возвращает новый API-ключ.

        Args:
            api_key_data: Данные для создания ключа.
            master_key: Мастер-ключ для авторизации создания.

        Returns:
            Схема с данными созданного ключа, включая сам ключ.

        Raises:
            MasterApiKeyError: Если предоставлен неверный мастер-ключ.
        """
        if master_key != self.settings.app.master_api_key.get_secret_value():
            raise MasterApiKeyError()

        full_key, db_prefix = generate_api_key(prefix="wfe")
        hashed_api_key = hash_password(full_key)

        created_key_obj = await self.api_key_repository.add_api_key(
            hashed_key=hashed_api_key,
            api_key_prefix=db_prefix,
            api_key_data=api_key_data,
        )

        return ApiKeyResponse(
            api_key=full_key,
            api_key_prefix=created_key_obj.api_key_prefix,
            issued_for=created_key_obj.issued_for,
            owner_email=created_key_obj.owner_email,
            comment=created_key_obj.comment,
            created_at=created_key_obj.created_at,
            expires_at=created_key_obj.expires_at,
            is_active=created_key_obj.is_active,
        )

    async def deactivate_api_key(
            self,
            api_key_prefix: str,
            master_key: str,
    ) -> ApiKeyStatusResponse:
        """
        Деактивирует API-ключ по его префиксу.

        Args:
            api_key_prefix: Префикс API-ключа для деактивации.
            master_key: Мастер-ключ для авторизации деактивации.

        Returns:
            Схема с данными деактивированного ключа.

        Raises:
            MasterApiKeyError: Если предоставлен неверный мастер-ключ.
            ApiKeyNotFoundError: Если API-ключ с таким префиксом не найден.
        """
        if master_key != self.settings.app.master_api_key.get_secret_value():
            raise MasterApiKeyError()

        deactivated_key_obj = await self.api_key_repository.update_is_active_by_prefix(
            api_key_prefix=api_key_prefix, is_active=False
        )

        if not deactivated_key_obj:
            raise ApiKeyNotFoundError(api_key_prefix=api_key_prefix)

        return ApiKeyStatusResponse(
            api_key_prefix=deactivated_key_obj.api_key_prefix,
            is_active=deactivated_key_obj.is_active,
        )

    async def get_all_api_keys(self, master_key: str) -> list[ApiKey]:
        """
        Возвращает список всех API-ключей.

        Args:
            master_key: Мастер-ключ для авторизации.

        Returns:
            Список объектов ApiKey.

        Raises:
            MasterApiKeyError: Если предоставлен неверный мастер-ключ.
        """
        if master_key != self.settings.app.master_api_key.get_secret_value():
            raise MasterApiKeyError()

        return await self.api_key_repository.get_all_keys()
