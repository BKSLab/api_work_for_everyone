from typing import Annotated

from fastapi import Depends

from dependencies.db_session import DbSessionDep
from repositories.blocklist_repository import BlocklistRepository
from repositories.region_repository import RegionRepository
from repositories.users_repository import UsersRepository
from repositories.vacancies_repository import VacanciesRepository


def get_region_repository(session: DbSessionDep) -> RegionRepository:
    return RegionRepository(session)


def get_vacancies_repository(session: DbSessionDep) -> VacanciesRepository:
    return VacanciesRepository(session)

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

UsersRepositoryDep = Annotated[
    UsersRepository, Depends(get_users_repository)
]

BlocklistRepositoryDep = Annotated[
    BlocklistRepository, Depends(get_blocklist_repository)
]
