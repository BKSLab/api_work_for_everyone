from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ApiKey(Base):
    """
    Модель для хранения информации об API-ключах, выданных клиентам.
    """

    __tablename__ = 'api_keys'

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор API-ключа.')
    hashed_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc='Хэшированное представление API-ключа для безопасного хранения.',
        comment='Односторонний хэш API-ключа (например, SHA-256), хранимый в базе данных.'
    )
    api_key_prefix: Mapped[str] = mapped_column(
        String(16),
        unique=True,
        nullable=False,
        doc='Префикс API-ключа для идентификации в логах без раскрытия полного ключа.',
        comment='Часть API-ключа (например, первые 8-16 символов), используемая для отладки и идентификации в логах.'
    )
    issued_for: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc='Описание клиента или сервиса, для которого был выдан API-ключ.',
        comment='Назначение API-ключа (например, "website", "telegram_bot", "mobile_app").'
    )
    owner_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc='Контактный адрес электронной почты владельца API-ключа.',
        comment='Адрес электронной почты лица или организации, ответственной за API-ключ.'
    )
    comment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Дополнительные внутренние комментарии или описание к API-ключу.',
        comment='Произвольный комментарий для внутреннего использования (например, цель использования, дата выдачи).'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc='Дата и время создания API-ключа.',
        comment='Метка времени создания записи API-ключа.'
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc='Дата и время истечения срока действия API-ключа.',
        comment='Метка времени, после которой API-ключ считается недействительным (необязательно).'
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc='Флаг активности API-ключа (активен/деактивирован).',
        comment='Булево значение, указывающее, является ли API-ключ активным (True) или деактивированным (False).'
    )

    def __repr__(self) -> str:
        return (
            f"<ApiKey(id={self.id}, issued_for='{self.issued_for}', "
            f"owner_email='{self.owner_email}', is_active={self.is_active})>"
        )
