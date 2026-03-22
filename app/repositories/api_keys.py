import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import Result, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.api_keys import ApiKey
from exceptions.repositories import ApiKeyRepositoryError
from schemas.api_key import ApiKeyCreate

logger = logging.getLogger(__name__)


class ApiKeyRepository:
    """Репозиторий для работы с API-ключами в базе данных."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_prefix(self, api_key_prefix: str) -> ApiKey | None:
        """Возвращает API-ключ по префиксу или None."""
        try:
            stmt = select(ApiKey).where(ApiKey.api_key_prefix == api_key_prefix)
            result: Result = await self.db_session.execute(statement=stmt)
            return result.scalars().first()
        except (SQLAlchemyError, Exception) as error:
            raise ApiKeyRepositoryError(
                error_details=f"Ошибка при получении API-ключа по префиксу '{api_key_prefix}'."
            ) from error

    async def add_api_key(
            self,
            hashed_key: str,
            api_key_prefix: str,
            api_key_data: ApiKeyCreate,
    ) -> ApiKey:
        """
        Создает и сохраняет новый API-ключ в базе данных.

        Args:
            hashed_key: Хэшированный API-ключ.
            api_key_prefix: Префикс API-ключа.
            api_key_data: Данные для создания ключа из схемы Pydantic.

        Returns:
            Созданный объект ApiKey.
        """
        try:
            new_key = ApiKey(
                hashed_key=hashed_key,
                api_key_prefix=api_key_prefix,
                issued_for=api_key_data.issued_for,
                owner_email=api_key_data.owner_email,
                comment=api_key_data.comment,
                expires_at=api_key_data.expires_at,
            )
            self.db_session.add(new_key)
            await self.db_session.commit()
            await self.db_session.refresh(new_key)
            return new_key
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "❌ Ошибка при создании API-ключа. Владелец: %s. Детали: %s",
                api_key_data.owner_email, error,
            )
            raise ApiKeyRepositoryError(
                error_details=f"Ошибка при создании API-ключа для {api_key_data.owner_email}."
            ) from error

    async def update_is_active_by_prefix(self, api_key_prefix: str, is_active: bool) -> ApiKey | None:
        """
        Обновляет статус активности API-ключа по его префиксу.

        Args:
            api_key_prefix: Префикс API-ключа.
            is_active: Новый статус активности (True - активен, False - деактивирован).

        Returns:
            Обновленный объект ApiKey или None, если ключ не найден.
        """
        try:
            api_key_obj = await self.get_by_prefix(api_key_prefix)
            if api_key_obj:
                api_key_obj.is_active = is_active
                await self.db_session.commit()
                await self.db_session.refresh(api_key_obj)
            return api_key_obj
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "❌ Ошибка при обновлении статуса API-ключа. Префикс: %s. Детали: %s",
                api_key_prefix, error,
            )
            raise ApiKeyRepositoryError(
                error_details=f"Ошибка при обновлении статуса API-ключа с префиксом '{api_key_prefix}'."
            ) from error

    async def get_all_keys(self) -> list[ApiKey]:
        """Возвращает список всех API-ключей из базы данных."""
        try:
            stmt = select(ApiKey).order_by(ApiKey.created_at.desc())
            result: Result = await self.db_session.execute(statement=stmt)
            return list(result.scalars().all())
        except (SQLAlchemyError, Exception) as error:
            raise ApiKeyRepositoryError(
                error_details="Ошибка при получении списка API-ключей."
            ) from error
