from .clients import HHClientDep, TVClientDep
from .db_session import get_db_session
from .repositories import (
    RegionRepositoryDep,
    VacanciesRepositoryDep,
)
from .services import RegionServiceDep, VacanciesServiceDep
