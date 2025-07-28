from typing import Annotated

from fastapi import Depends

from dependencies.db_session import DbSessionDep
from repositories.region_repository import RegionRepository
from repositories.vacancies_repository import VacanciesRepository


def get_region_repository(session: DbSessionDep) -> RegionRepository:
    return RegionRepository(session)


def get_vacancies_repository(session: DbSessionDep) -> VacanciesRepository:
    return VacanciesRepository(session)


RegionRepositoryDep = Annotated[
    RegionRepository, Depends(get_region_repository)
]

VacanciesRepositoryDep = Annotated[
    VacanciesRepository, Depends(get_vacancies_repository)
]
