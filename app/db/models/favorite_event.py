from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FavoriteEvent(Base):
    """
    Лог событий добавления/удаления вакансий в избранное.
    Одна запись = одно действие пользователя (add / remove).
    Вакансия сохраняется полностью — данные не теряются после удаления из избранного.
    """

    __tablename__ = 'favorite_events'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        comment='Уникальный идентификатор события.'
    )
    user_id: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
        comment='ID пользователя (Telegram ID, email и т.д.).'
    )
    vacancy_id: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
        comment='ID вакансии на сайте-источнике.'
    )
    action: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment='Действие: "add" — добавлено в избранное, "remove" — удалено.'
    )
    vacancy_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='Название вакансии.'
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='Название работодателя.'
    )
    vacancy_source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment='Источник вакансии: hh.ru или trudvsem.ru.'
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment='Город / населённый пункт вакансии.'
    )
    category: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='Категория вакансии.'
    )
    salary: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
        comment='Информация о зарплате.'
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment='Полное описание вакансии на момент добавления в избранное.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='Дата и время события.'
    )

    def __repr__(self) -> str:
        return (
            f"<FavoriteEvent(id={self.id}, user_id='{self.user_id}', "
            f"vacancy_id='{self.vacancy_id}', action='{self.action}', "
            f"created_at='{self.created_at}')>"
        )
