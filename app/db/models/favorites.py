from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base_vacancy import BaseVacancy


class FavoriteVacancies(BaseVacancy):
    """
    Модель для хранения информации о вакансиях, добавленных пользователем в избранное,
    """

    __tablename__ = 'favorite_vacancies'

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        doc='ID пользователя.'
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'vacancy_id', name='unique_user_id_vacancy_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<FavoriteVacancies(id={self.id}, vacancy_id='{self.vacancy_id}', "
            f"source='{self.vacancy_source}', user_id='{self.user_id}'>"
        )
