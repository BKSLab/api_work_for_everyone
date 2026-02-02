from sqlalchemy import UniqueConstraint

from .base_vacancy import BaseVacancy


class Vacancies(BaseVacancy):
    """
    Модель для хранения информации о вакансиях,
    """

    __tablename__ = 'vacancies'

    __table_args__ = (
        UniqueConstraint('vacancy_id', name='uq_vacancies_vacancy_id'),
    )

    def __repr__(self) -> str:
        return (
            f"<Vacancies(id={self.id}, vacancy_id='{self.vacancy_id}', "
            f"name='{self.name}', source='{self.vacancy_source}')>"
        )
