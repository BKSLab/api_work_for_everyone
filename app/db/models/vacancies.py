from datetime import datetime

from sqlalchemy import DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base_vacancy import BaseVacancy


class Vacancies(BaseVacancy):
    """
    Модель для хранения информации о вакансиях,
    """

    __tablename__ = 'vacancies'

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='Дата последнего обновления списка вакансий по локации'
    )

    __table_args__ = (
        UniqueConstraint(
            'vacancy_id', 'location', name='unique_vacancies_vacancy_id__location'),
    )

    def __repr__(self) -> str:
        return (
            f"<Vacancies(id={self.id}, vacancy_id='{self.vacancy_id}', "
            f"name='{self.name}', source='{self.vacancy_source}')>"
        )
