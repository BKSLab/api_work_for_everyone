from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Vacancies(Base):
    """
    Модель для хранения информации о вакансиях,
    """

    __tablename__ = 'vacancies'

    id: Mapped[int] = mapped_column(primary_key=True)
    vacancy_id: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        unique=True,
        nullable=False,
        doc='id вакансии на сайте источнике.'
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Место нахождение вакансии.'
    )
    name: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Название вакансии.'
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Описание вакансии.'
    )
    salary: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Заработная плата.'
    )
    vacancy_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Ссылка на вакансию.'
    )
    vacancy_source: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=False,
        doc='Источник вакансии.'
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Наименование работодателя.'
    )
    employer_location: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Адрес места нахождения работодателя.'
    )
    employer_phone: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=False,
        doc='Номер телефона работодателя.'
    )
    employer_code: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=False,
        doc='id работодателя на сайте источника.'
    )
    experience_required: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Требования к соискателю.'
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=False,
        doc='Категория вакансии.'
    )
    employment_type: Mapped[Optional[str]] = mapped_column(
        String(length=200),
        nullable=False,
        doc='Тип занятости.'
    )
    schedule: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Требование к образованию.'
    )

    def __repr__(self) -> str:
        return (
            f"<Vacansies(id={self.id}, vacancy_id='{self.vacancy_id}', "
            f"name='{self.name}', source='{self.vacancy_source}')>"
        )
