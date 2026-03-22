import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.assistant_session import AssistantSession
from exceptions.repositories import AssistantSessionRepositoryError

logger = logging.getLogger(__name__)


class AssistantSessionRepository:
    """Репозиторий для сохранения сессий обращений к AI-ассистенту."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def save_session(
        self,
        session_type: str,
        vacancy_id: str,
        vacancy_name: str,
        result: str,
        llm_model: str,
        employer_name: str | None = None,
        employer_location: str | None = None,
        employment: str | None = None,
        salary: str | None = None,
        description: str | None = None,
        answers: list[dict[str, Any]] | None = None,
    ) -> None:
        """Сохраняет запись о сессии обращения к AI-ассистенту.

        Args:
            session_type: Тип вызова ассистента (например, 'cover_letter_by_vacancy').
            vacancy_id: Идентификатор вакансии.
            vacancy_name: Название вакансии.
            result: Ответ LLM (HTML-текст или JSON-строка анкеты).
            llm_model: Идентификатор использованной модели LLM.
            employer_name: Название работодателя.
            employer_location: Адрес работодателя.
            employment: Тип занятости.
            salary: Информация о зарплате.
            description: Описание вакансии.
            answers: Ответы соискателя на анкету (только для by_questionnaire сессий).

        Raises:
            AssistantSessionRepositoryError: При ошибке сохранения в БД.
        """
        try:
            session = AssistantSession(
                session_type=session_type,
                vacancy_id=vacancy_id,
                vacancy_name=vacancy_name,
                employer_name=employer_name,
                employer_location=employer_location,
                employment=employment,
                salary=salary,
                description=description,
                answers=answers,
                result=result,
                llm_model=llm_model,
            )
            self.db_session.add(session)
            await self.db_session.commit()
            logger.info(
                "💾 Сессия ассистента сохранена. Тип: %s, ID вакансии: %s.",
                session_type, vacancy_id,
            )
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "❌ Ошибка при сохранении сессии ассистента. Тип: %s, ID вакансии: %s. Детали: %s",
                session_type, vacancy_id, error,
            )
            raise AssistantSessionRepositoryError(
                error_details=f"Ошибка при сохранении сессии ассистента типа '{session_type}'."
            ) from error
