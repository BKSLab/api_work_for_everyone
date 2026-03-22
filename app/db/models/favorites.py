from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base_vacancy import BaseVacancy


class FavoriteVacancies(BaseVacancy):
    """
    Модель для хранения информации о вакансиях, добавленных пользователем в избранное,
    """

    __tablename__ = 'favorite_vacancies'

    user_id: Mapped[str] = mapped_column(
        String(length=300),
        nullable=False,
        doc='ID пользователя (Telegram ID, email, любой другой внещний ID).',
        comment='ID пользователя (Telegram ID, email, любой другой внещний ID) для связи вакансии.'
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment='Дата последнего обновления данных вакансии из источника'
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'vacancy_id', name='unique_user_id_vacancy_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<FavoriteVacancies(id={self.id}, vacancy_id='{self.vacancy_id}', "
            f"source='{self.vacancy_source}', user_id='{self.user_id}'>"
        )
