import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.users import EmailVerificationCode, PasswordResetCode, User
from exceptions.repository_exceptions import UsersRepositoryError

logger = logging.getLogger(__name__)


class UsersRepository:
    """Класс для взаимодействия с БД, для работы с пользователями."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_user(
        self,
        email: str,
        password_hash: str,
        username: str | None = None
    ) -> User:
        """
        Создает нового пользователя с неактивным статусом до подтверждения почты.
        """
        try:
            stmt = (
                insert(User)
                .values(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    is_active=False,   # Пользователь неактивен до подтверждения
                    is_verified=False,
                    created_at=datetime.now(timezone.utc),
                )
                .returning(User)
            )

            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.scalar_one()

        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при создании записи о пользователе с email %s: %s",
                email, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def update_user(
            self,
            user_id: int,
            password_hash: str,
            username: str | None = None
    ) -> None:
        """
        Обновляет данные пользователя (имя и хэш пароля).
        """
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(
                    username=username,
                    password_hash=password_hash
                )
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при обновлении данных пользователя с ID %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def get_user_by_email(self, email: str, is_verified: bool = False) -> User | None:
        """
        Возвращает пользователя по email.
        """
        try:
            stmt = select(User).where(
                User.email == email,
                User.is_verified == is_verified,
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(
                "Ошибка при получении пользователя по email %s: %s",
                email, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def get_user_only_email(self, email: str) -> User | None:
        """
        Возвращает пользователя по email.
        """
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(
                "Ошибка при получении пользователя по email %s: %s",
                email, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def save_verification_code(
        self,
        user_id: int,
        code: str,
        expires_in_minutes: int = 15
    ) -> None:
        """
        Создает новый код верификации для пользователя с заданным временем истечения.
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=expires_in_minutes)

            stmt = (
                insert(EmailVerificationCode)
                .values(
                    user_id=user_id,
                    code=code,
                    created_at=now,
                    expires_at=expires_at
                )
            )

            await self.db_session.execute(stmt)
            await self.db_session.commit()

            logger.info(
                "Код подтверждения для пользователя %s успешно создан (действителен до %s)",
                user_id, expires_at.isoformat()
            )

        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при создании кода верификации для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def find_verification_code(self, user_id: int, code: str) -> EmailVerificationCode | None:
        """
        Находит код верификации для пользователя без проверки срока его действия.
        """
        try:
            stmt = select(EmailVerificationCode).where(
                EmailVerificationCode.user_id == user_id,
                EmailVerificationCode.code == code
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(
                "Ошибка при поиске кода верификации для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def confirm_user_email(self, user_id: int) -> None:
        """Подтверждает почту пользователя."""
        try:
            stmt = update(User).where(
                User.id == user_id
            ).values(is_verified=True, is_active=True)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при подтверждении почты для пользователя %s: %s",
                user_id, error, exc_info=True
            )
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
            logger.error(
                "Ошибка при удалении кодов верификации для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def save_password_reset_code(
        self,
        user_id: int,
        code: str,
        expires_in_minutes: int = 30
    ) -> None:
        """
        Создает новый код сброса пароля для пользователя с заданным временем истечения.
        """
        try:
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=expires_in_minutes)

            stmt = (
                insert(PasswordResetCode)
                .values(
                    user_id=user_id,
                    code=code,
                    created_at=now,
                    expires_at=expires_at
                )
            )

            await self.db_session.execute(stmt)
            await self.db_session.commit()

            logger.info(
                "Код сброса пароля для пользователя %s успешно создан (действителен до %s)",
                user_id, expires_at.isoformat()
            )

        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при создании кода сброса пароля для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def get_password_reset_code(self, user_id: int, code: str) -> PasswordResetCode | None:
        """
        Получает код сброса пароля для пользователя.
        """
        try:
            stmt = select(PasswordResetCode).where(
                PasswordResetCode.user_id == user_id,
                PasswordResetCode.code == code,
                PasswordResetCode.expires_at > datetime.now(timezone.utc)
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(
                "Ошибка при получении кода сброса пароля для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def find_password_reset_code(self, user_id: int, code: str) -> PasswordResetCode | None:
        """
        Находит код сброса пароля для пользователя без проверки срока его действия.
        """
        try:
            stmt = select(PasswordResetCode).where(
                PasswordResetCode.user_id == user_id,
                PasswordResetCode.code == code,
            )
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            logger.error(
                "Ошибка при поиске кода сброса пароля для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def delete_password_reset_codes(self, user_id: int) -> None:
        """
        Удаляет все коды сброса пароля пользователя.
        """
        try:
            stmt = delete(PasswordResetCode).where(PasswordResetCode.user_id == user_id)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при удалении кодов сброса пароля для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error

    async def update_user_password(self, user_id: int, new_password_hash: str) -> None:
        """
        Обновляет хэш пароля пользователя.
        """
        try:
            stmt = update(User).where(
                User.id == user_id
            ).values(password_hash=new_password_hash)
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "Ошибка при обновлении пароля для пользователя %s: %s",
                user_id, error, exc_info=True
            )
            raise UsersRepositoryError(cause=error) from error
