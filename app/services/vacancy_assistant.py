import logging
from typing import TypeVar

from pydantic import BaseModel

from clients.llm import LlmClient
from services.prompts.assistant_vera import (
    GEN_COVER_LETTER_BY_ANSWERS_PROMPT,
    GEN_COVER_LETTER_BY_VACANCY_PROMPT,
    GEN_LETTER_QUESTIONNAIRE_PROMPT,
    GEN_RESUME_QUESTIONNAIRE_PROMPT,
    GEN_RESUME_TIPS_BY_ANSWERS_PROMPT,
    GEN_RESUME_TIPS_BY_VACANCY_PROMPT,
)

logger = logging.getLogger(__name__)

PydanticModel = TypeVar("PydanticModel", bound=BaseModel)


class VacancyAiAssistant:
    """
    Ассистент для помощи в составлении сопроводительных писем и
    рекомендаций для резюме на основе данных о вакансии.
    """

    def __init__(self, llm_client: LlmClient):
        """Инициализация ассистента."""
        self.llm_client = llm_client

    def _build_vacancy_content(self, vacancy: dict) -> dict:
        """Формирует словарь с данными вакансии для передачи в LLM."""
        return {
            "vacancy_name": vacancy.get("vacancy_name"),
            "employer_name": vacancy.get("employer_name"),
            "employer_location": vacancy.get("employer_location"),
            "employment": vacancy.get("employment"),
            "salary": vacancy.get("salary"),
            "description": vacancy.get("description"),
            "experience_required": vacancy.get("experience_required"),
            "requirements": vacancy.get("requirements"),
            "work_format": vacancy.get("work_format"),
        }

    async def gen_cover_letter_by_vacancy(self, vacancy: dict, model: str | None = None) -> str:
        """
        Генерирует сопроводительное письмо на основе данных вакансии.
        """
        content = self._build_vacancy_content(vacancy)
        llm_responce = await self.llm_client.get_llm_response(
            content=str(content), prompt=GEN_COVER_LETTER_BY_VACANCY_PROMPT, model=model
        )
        return llm_responce

    async def gen_resume_tips_by_vacancy(self, vacancy: dict, model: str | None = None) -> str:
        """
        Генерирует рекомендации по составлению резюме на основе данных вакансии.
        """
        content = self._build_vacancy_content(vacancy)
        llm_responce = await self.llm_client.get_llm_response(
            content=str(content), prompt=GEN_RESUME_TIPS_BY_VACANCY_PROMPT, model=model
        )
        return llm_responce

    async def gen_letter_questionnaire(
        self, vacancy: dict, schema: type[PydanticModel], model: str | None = None
    ) -> PydanticModel:
        """
        Генерирует анкету по данным вакансии для последующего
        составления сопроводительного письма.
        """
        content = self._build_vacancy_content(vacancy)
        llm_responce = await self.llm_client.get_llm_response(
            content=str(content), prompt=GEN_LETTER_QUESTIONNAIRE_PROMPT, schema=schema, model=model
        )
        return llm_responce

    async def gen_resume_questionnaire(
        self, vacancy: dict, schema: type[PydanticModel], model: str | None = None
    ) -> PydanticModel:
        """
        Генерирует анкету по данным вакансии для последующего
        составления рекомендаций по резюме.
        """
        content = self._build_vacancy_content(vacancy)
        llm_responce = await self.llm_client.get_llm_response(
            content=str(content), prompt=GEN_RESUME_QUESTIONNAIRE_PROMPT, schema=schema, model=model
        )
        return llm_responce

    async def gen_cover_letter_by_questionnaire(
        self, questionnaire: list[dict], vacancy: dict, model: str | None = None
    ) -> str:
        """
        Генерирует сопроводительное письмо на основе анкеты и данных вакансии.
        """
        content_vacancy = self._build_vacancy_content(vacancy)
        content = f"Данные вакансии:\n{content_vacancy}\n\nДанные заполненной анкеты по вакансии:\n{questionnaire}"
        llm_responce = await self.llm_client.get_llm_response(
            content=str(content), prompt=GEN_COVER_LETTER_BY_ANSWERS_PROMPT, model=model
        )
        return llm_responce

    async def gen_resume_tips_by_questionnaire(
        self, questionnaire: list[dict], vacancy: dict, model: str | None = None
    ) -> str:
        """
        Генерирует рекомендации по резюме на основе анкеты и данных вакансии.
        """
        content_vacancy = self._build_vacancy_content(vacancy)
        content = f"Данные вакансии:\n{content_vacancy}\n\nДанные заполненной анкеты по вакансии:\n{questionnaire}"
        llm_responce = await self.llm_client.get_llm_response(
            content=str(content), prompt=GEN_RESUME_TIPS_BY_ANSWERS_PROMPT, model=model
        )
        return llm_responce
