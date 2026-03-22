from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class AssistantSession(Base):
    """
    Модель для хранения сессий обращений к AI-ассистенту.
    Каждая запись соответствует одному вызову LLM: входные данные вакансии,
    ответы соискателя (если есть) и сгенерированный результат.
    """

    __tablename__ = 'assistant_sessions'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        doc='Уникальный идентификатор сессии.',
        comment='Уникальный идентификатор записи сессии AI-ассистента.',
    )
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc='Тип сессии — какой из методов ассистента был вызван.',
        comment=(
            'Тип вызова ассистента. Возможные значения: cover_letter_by_vacancy, '
            'resume_tips_by_vacancy, letter_questionnaire, resume_questionnaire, '
            'cover_letter_by_questionnaire, resume_tips_by_questionnaire.'
        ),
    )

    # Данные вакансии, отправленные в LLM
    vacancy_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc='Идентификатор вакансии, по которой был вызван ассистент.',
        comment='ID вакансии из источника (hh.ru или trudvsem.ru). Используется для фильтрации.',
    )
    vacancy_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc='Название вакансии, отправленное в LLM.',
        comment='Название должности/вакансии, переданное в промпт LLM.',
    )
    employer_name: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Название работодателя, отправленное в LLM.',
        comment='Наименование организации-работодателя, переданное в промпт LLM.',
    )
    employer_location: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Адрес работодателя, отправленный в LLM.',
        comment='Адрес рабочего места, переданный в промпт LLM.',
    )
    employment: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='График/тип занятости, отправленный в LLM.',
        comment='Тип занятости (полный день, удалённо и т.д.), переданный в промпт LLM.',
    )
    salary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Информация о зарплате, отправленная в LLM.',
        comment='Зарплатные данные вакансии, переданные в промпт LLM.',
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc='Описание вакансии, отправленное в LLM.',
        comment='Полный текст описания вакансии (обязанности, требования), переданный в промпт LLM.',
    )

    # Ответы соискателя (только для by_questionnaire методов)
    answers: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        doc='Ответы соискателя на вопросы анкеты. Заполнен только для by_questionnaire сессий.',
        comment='JSON-массив ответов соискателя: [{id, text, answer}]. NULL для остальных типов сессий.',
    )

    # Результат LLM
    result: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc='Ответ LLM: HTML-текст (письмо/рекомендации) или JSON-строка (анкета).',
        comment='Сырой результат, возвращённый LLM. Для questionnaire-типов — JSON, для остальных — HTML.',
    )

    # Метаданные
    llm_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc='Идентификатор модели LLM, использованной в сессии.',
        comment='Название/ID модели LLM (например, "deepseek-r1"), которая сгенерировала результат.',
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc='Дата и время создания сессии.',
        comment='Метка времени создания записи сессии AI-ассистента.',
    )

    def __repr__(self) -> str:
        return (
            f"<AssistantSession(id={self.id}, session_type='{self.session_type}', "
            f"vacancy_id='{self.vacancy_id}', created_at='{self.created_at}')>"
        )
