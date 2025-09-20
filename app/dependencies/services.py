from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.users_service import UsersService
from core.config_logger import logger
from dependencies.clients import HHClientDep, TVClientDep
from dependencies.repositories import RegionRepositoryDep, UsersRepositoryDep, VacanciesRepositoryDep
from services.region_service import RegionService
from services.vacancies_service import VacanciesService


async def get_users_service(
    users_repository: UsersRepositoryDep
) -> UsersService:
    """Генератор для создания сессии базы данных."""
    return UsersService(
        users_repository=users_repository
    )


async def get_region_service(
    region_repository: RegionRepositoryDep
) -> RegionService:
    """Генератор для создания сессии базы данных."""
    return RegionService(
        region_repository=region_repository
    )


RegionServiceDep = Annotated[
    RegionService, Depends(get_region_service)
]
UsersServiceDep = Annotated[
    UsersService, Depends(get_users_service)
]


async def get_vacancies_service(
    region_service: RegionServiceDep,
    vacancies_repository: VacanciesRepositoryDep,
    hh_client_api: HHClientDep,
    tv_client_api: TVClientDep,
) -> VacanciesService:
    """Фабрика для создания экземпляра сервиса работы с вакансиями."""
    return VacanciesService(
        region_service=region_service,
        vacancies_repository=vacancies_repository,
        hh_client_api=hh_client_api,
        tv_client_api=tv_client_api,
    )


VacanciesServiceDep = Annotated[
    VacanciesService, Depends(get_vacancies_service)
]


async def check_db_connection(db_session: AsyncSession) -> bool:
    """Проверяет доступность БД и выполнение простого запроса."""
    try:
        await db_session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f'Database connection check failed: {str(e)}')
        return False
