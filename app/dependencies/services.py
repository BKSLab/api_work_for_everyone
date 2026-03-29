from typing import Annotated

from fastapi import Depends

from core.settings import Settings, get_settings
from dependencies.clients import HHClientDep, LlmClientDep, TVClientDep
from dependencies.repositories import (
    ApiKeyRepositoryDep,
    AssistantSessionRepositoryDep,
    FavoriteEventRepositoryDep,
    FavoritesRepositoryDep,
    RegionRepositoryDep,
    SearchEventRepositoryDep,
    VacanciesRepositoryDep,
)
from services.api_keys import ApiKeyService
from services.parsing_vacancies import VacanciesParsingService
from services.regions import RegionService
from services.vacancies import VacanciesService
from services.vacancy_assistant import VacancyAiAssistant


async def get_region_service(
    region_repository: RegionRepositoryDep
) -> RegionService:
    """Генератор для создания сессии базы данных."""
    return RegionService(
        region_repository=region_repository
    )


async def get_vacancies_parsing_service() -> VacanciesParsingService:
    """Зависимость для сервиса парсинга данных вакансий."""
    return VacanciesParsingService()


async def get_vacancy_ai_assistant(
    llm_client: LlmClientDep
) -> VacancyAiAssistant:
    """Зависимость для класса сервиса VacancyAiAssistant."""
    return VacancyAiAssistant(
        llm_client=llm_client
    )


RegionServiceDep = Annotated[
    RegionService, Depends(get_region_service)
]

VacanciesParsingServiceDep = Annotated[
    VacanciesParsingService, Depends(get_vacancies_parsing_service)
]

VacancyAiAssistantDep = Annotated[
    VacancyAiAssistant, Depends(get_vacancy_ai_assistant)
]


async def get_vacancies_service(
    region_service: RegionServiceDep,
    vacancies_repository: VacanciesRepositoryDep,
    favorites_repository: FavoritesRepositoryDep,
    favorite_event_repository: FavoriteEventRepositoryDep,
    assistant_session_repository: AssistantSessionRepositoryDep,
    search_event_repository: SearchEventRepositoryDep,
    hh_client_api: HHClientDep,
    tv_client_api: TVClientDep,
    vacancies_parser: VacanciesParsingServiceDep,
    vacancy_ai_assistant: VacancyAiAssistantDep,
) -> VacanciesService:
    """Фабрика для создания экземпляра сервиса работы с вакансиями."""
    return VacanciesService(
        region_service=region_service,
        vacancies_repository=vacancies_repository,
        favorites_repository=favorites_repository,
        favorite_event_repository=favorite_event_repository,
        assistant_session_repository=assistant_session_repository,
        search_event_repository=search_event_repository,
        hh_client_api=hh_client_api,
        tv_client_api=tv_client_api,
        vacancies_parser=vacancies_parser,
        vacancy_ai_assistant=vacancy_ai_assistant,
    )


VacanciesServiceDep = Annotated[
    VacanciesService, Depends(get_vacancies_service)
]


async def get_api_key_service(
    api_key_repository: ApiKeyRepositoryDep,
    settings: Settings = Depends(get_settings),
) -> ApiKeyService:
    """Фабрика для создания экземпляра сервиса работы с API-ключами."""
    return ApiKeyService(
        api_key_repository=api_key_repository,
        settings=settings,
    )


ApiKeyServiceDep = Annotated[
    ApiKeyService, Depends(get_api_key_service)
]

