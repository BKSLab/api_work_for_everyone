from typing import Annotated

from fastapi import Depends

from dependencies.db_session import DbSessionDep
from repositories.api_keys import ApiKeyRepository
from repositories.assistant_session import AssistantSessionRepository
from repositories.favorites import FavoritesRepository
from repositories.regions import RegionRepository
from repositories.search_event import SearchEventRepository
from repositories.vacancies import VacanciesRepository


def get_region_repository(session: DbSessionDep) -> RegionRepository:
    return RegionRepository(session)


def get_vacancies_repository(session: DbSessionDep) -> VacanciesRepository:
    return VacanciesRepository(session)


def get_favorites_repository(session: DbSessionDep) -> FavoritesRepository:
    return FavoritesRepository(session)


RegionRepositoryDep = Annotated[
    RegionRepository, Depends(get_region_repository)
]

VacanciesRepositoryDep = Annotated[
    VacanciesRepository, Depends(get_vacancies_repository)
]

FavoritesRepositoryDep = Annotated[
    FavoritesRepository, Depends(get_favorites_repository)
]


def get_api_key_repository(session: DbSessionDep) -> ApiKeyRepository:
    return ApiKeyRepository(session)


ApiKeyRepositoryDep = Annotated[
    ApiKeyRepository, Depends(get_api_key_repository)
]


def get_assistant_session_repository(session: DbSessionDep) -> AssistantSessionRepository:
    return AssistantSessionRepository(session)


AssistantSessionRepositoryDep = Annotated[
    AssistantSessionRepository, Depends(get_assistant_session_repository)
]


def get_search_event_repository(session: DbSessionDep) -> SearchEventRepository:
    return SearchEventRepository(session)


SearchEventRepositoryDep = Annotated[
    SearchEventRepository, Depends(get_search_event_repository)
]
