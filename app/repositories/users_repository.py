import logging
from datetime import datetime, timezone
from sqlalchemy import insert, select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions.repository_exceptions import UsersRepositoryError
from db.models.users import User, EmailVerificationCode
from core.config_logger import logger


class UsersRepository:
    """Класс для взаимодействия с БД, для работы с пользователями."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(self, user_data: dict) -> User:
        """
        Создает нового пользователя.
        """
        try:
            stmt = insert(User).values(**user_data).returning(User)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(f'Ошибка при создании пользователя: {error}')
            raise UsersRepositoryError(cause=error) from error

    async def get_user(self, email: str, username: str) -> User | None:
        """
        Возвращает пользователя по email и username.
        """
        try:
            stmt = select(User).where(
                User.email == email,
                User.username == username
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(f'Ошибка при получении пользователя по email "{email}": {error}')
            raise UsersRepositoryError(cause=error) from error

    async def create_verification_code(self, code_data: dict) -> EmailVerificationCode:
        """
        Создает новый код верификации для пользователя.
        """
        try:
            stmt = insert(EmailVerificationCode).values(**code_data).returning(EmailVerificationCode)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(f'Ошибка при создании кода верификации: {error}')
            raise UsersRepositoryError(cause=error) from error

    async def get_verification_code(self, user_id: int, code: str) -> EmailVerificationCode | None:
        """
        Получает код верификации для пользователя.
        """
        try:
            stmt = select(EmailVerificationCode).where(
                EmailVerificationCode.user_id == user_id,
                EmailVerificationCode.code == code,
                EmailVerificationCode.expires_at > datetime.now(timezone.utc)
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(f'Ошибка при получении кода верификации: {error}')
            raise UsersRepositoryError(cause=error) from error

    async def confirm_user_email(self, user_id: int) -> None:
        """
        Подтверждает почту пользователя.
        """
        try:
            stmt = update(User).where(User.id == user_id).values(is_verified=True)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(f'Ошибка при подтверждении почты для пользователя {user_id}: {error}')
            raise UsersRepositoryError(cause=error) from error

    async def delete_verification_codes(self, user_id: int) -> None:
        """
        Удаляет все коды верификации пользователя (например, после успешной активации).
        """
        try:
            stmt = delete(EmailVerificationCode).where(EmailVerificationCode.user_id == user_id)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(f'Ошибка при удалении кодов верификации для пользователя {user_id}: {error}')
            raise UsersRepositoryError(cause=error) from error
