from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class User(Base):
    """
    Модель для хранения информации о пользователях системы.
    """

    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=True,
        doc='Отображаемое имя пользователя.'
    )
    email: Mapped[str] = mapped_column(
        String(length=255),
        unique=True,
        nullable=False,
        index=True,
        doc='Электронная почта пользователя.'
    )
    password_hash: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        doc='Хэш пароля пользователя.'
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        doc='Флаг активности пользователя.'
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc='Флаг подтверждения почты.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc='Дата и время регистрации.'
    )

    def __repr__(self) -> str:
        return f'<User(email={self.email}, verified={self.is_verified})>'


class EmailVerificationCode(Base):
    """
    Модель для хранения кодов подтверждения почты.
    """

    __tablename__ = 'email_verification_codes'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        doc='ID пользователя.'
    )
    code: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        doc='Код подтверждения.'
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc='Время истечения действия кода.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc='Дата и время создания кода.'
    )

    def __repr__(self) -> str:
        return f'<EmailVerificationCode(user_id={self.user_id}, code={self.code})>'


class PasswordResetCode(Base):
    """
    Модель для хранения кодов сброса пароля.
    """

    __tablename__ = 'password_reset_codes'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        doc='ID пользователя.'
    )
    code: Mapped[str] = mapped_column(
        String(length=20),
        nullable=False,
        doc='Код сброса пароля.'
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc='Время истечения действия кода.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc='Дата и время создания кода.'
    )

    def __repr__(self) -> str:
        return f'<PasswordResetCode(user_id={self.user_id}, code={self.code})>'
