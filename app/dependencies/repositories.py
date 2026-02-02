from typing import Annotated

from fastapi import Depends

from dependencies.db_session import DbSessionDep
from repositories.blocklist_repository import BlocklistRepository
from repositories.favorites import FavoritesRepository
from repositories.regions import RegionRepository
from repositories.users import UsersRepository
from repositories.vacancies import VacanciesRepository


def get_region_repository(session: DbSessionDep) -> RegionRepository:
    return RegionRepository(session)


def get_vacancies_repository(session: DbSessionDep) -> VacanciesRepository:
    return VacanciesRepository(session)


def get_favorites_repository(session: DbSessionDep) -> FavoritesRepository:
    return FavoritesRepository(session)


def get_users_repository(session: DbSessionDep) -> UsersRepository:
    return UsersRepository(session)


def get_blocklist_repository(session: DbSessionDep) -> BlocklistRepository:
    return BlocklistRepository(session)


RegionRepositoryDep = Annotated[
    RegionRepository, Depends(get_region_repository)
]

VacanciesRepositoryDep = Annotated[
    VacanciesRepository, Depends(get_vacancies_repository)
]

FavoritesRepositoryDep = Annotated[
    FavoritesRepository, Depends(get_favorites_repository)
]

UsersRepositoryDep = Annotated[
    UsersRepository, Depends(get_users_repository)
]

BlocklistRepositoryDep = Annotated[
    BlocklistRepository, Depends(get_blocklist_repository)
]
