from .clients import HHClientDep, TVClientDep
from .db_session import get_db_session
from .jwt import JWTManagerDep
from .repositories import (
    RegionRepositoryDep,
    UsersRepositoryDep,
    VacanciesRepositoryDep,
)
from .services import RegionServiceDep, UsersServiceDep, VacanciesServiceDep
