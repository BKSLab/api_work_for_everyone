from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BaseVacancy(Base):
    """
    Абстрактная базовая модель для хранения данных вакансии.
    """
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, comment='Уникальный идентификатор записи')
    vacancy_id: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='id вакансии на сайте источнике.',
        comment='Идентификатор вакансии на сайте-источнике (например, hh.ru, trudvsem.ru)'
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Место нахождение вакансии.',
        comment='Город или населенный пункт, где расположена вакансия'
    )
    vacancy_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Название вакансии.',
        comment='Название или должность вакансии'
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(length=50),
        nullable=True,
        doc='Статус вакансии.',
        comment='Статус вакансии (actual, archival, not_found)'
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Описание вакансии.',
        comment='Полное описание требований и обязанностей вакансии'
    )
    salary: Mapped[Optional[str]] = mapped_column(
        String(length=300),
        nullable=False,
        doc='Заработная плата.',
        comment='Информация о заработной плате (например, "от 50000", "до 100000", "по договоренности")'
    )
    vacancy_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Ссылка на вакансию.',
        comment='Полный URL-адрес вакансии на сайте-источнике'
    )
    vacancy_source: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=False,
        doc='Источник вакансии.',
        comment='Название сайта-источника вакансии (например, "hh.ru", "trudvsem.ru")'
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Наименование работодателя.',
        comment='Наименование компании-работодателя'
    )
    employer_location: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Адрес места нахождения работодателя.',
        comment='Адрес расположения работодателя'
    )
    employer_phone: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Номер телефона работодателя.',
        comment='Контактный номер телефона работодателя'
    )
    employer_code: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        nullable=False,
        doc='id работодателя на сайте источника.',
        comment='Идентификатор работодателя на сайте-источнике'
    )
    employer_email: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Email работодателя.',
        comment='Контактный email работодателя'
    )
    contact_person: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Контактное лицо.',
        comment='ФИО контактного лица работодателя'
    )
    employment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Тип занятости.',
        comment='Тип занятости (например, "Полная", "Частичная", "Проектная")'
    )
    schedule: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='График работы.',
        comment='График работы (например, "Полный день", "Гибкий график", "Удаленная работа")'
    )
    work_format: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Формат работы.',
        comment='Формат выполнения работы (например, "Офис", "Разъездной", "Удалённо")'
    )
    experience_required: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Требования к соискателю.',
        comment='Требуемый опыт работы для соискателя'
    )
    requirements: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Требования к кандидату.',
        comment='Конкретные требования к кандидату: навыки, знания, компетенции'
    )
    category: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=False,
        doc='Категория вакансии.',
        comment='Категория, к которой относится вакансия (например, "IT", "Продажи")'
    )
    social_protected: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Признак соц. защищённости.',
        comment='Признак вакансии для социально защищённых категорий граждан'
    )
