from typing import Annotated

from fastapi import Depends

from dependencies.clients import HHClientDep, TVClientDep
from dependencies.repositories import (
    BlocklistRepositoryDep,
    FavoritesRepositoryDep,
    RegionRepositoryDep,
    UsersRepositoryDep,
    VacanciesRepositoryDep,
)
from services.blocklist import BlocklistService
from services.parsing_vacancies import VacanciesParsingService
from services.regions import RegionService
from services.users import UsersService
from services.vacancies import VacanciesService


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

async def get_blocklist_service(
    blocklist_repository: BlocklistRepositoryDep
) -> BlocklistService:
    """Зависимость для сервиса черного списка токенов."""
    return BlocklistService(blocklist_repo=blocklist_repository)


async def get_vacancies_parsing_service() -> VacanciesParsingService:
    """Зависимость для сервиса парсинга данных вакансий."""
    return VacanciesParsingService()


RegionServiceDep = Annotated[
    RegionService, Depends(get_region_service)
]
UsersServiceDep = Annotated[
    UsersService, Depends(get_users_service)
]
BlocklistServiceDep = Annotated[
    BlocklistService, Depends(get_blocklist_service)
]
VacanciesParsingServiceDep = Annotated[
    VacanciesParsingService, Depends(get_vacancies_parsing_service)
]


async def get_vacancies_service(
    region_service: RegionServiceDep,
    vacancies_repository: VacanciesRepositoryDep,
    favorites_repository: FavoritesRepositoryDep,
    hh_client_api: HHClientDep,
    tv_client_api: TVClientDep,
    vacancies_parser: VacanciesParsingServiceDep,
) -> VacanciesService:
    """Фабрика для создания экземпляра сервиса работы с вакансиями."""
    return VacanciesService(
        region_service=region_service,
        vacancies_repository=vacancies_repository,
        favorites_repository=favorites_repository,
        hh_client_api=hh_client_api,
        tv_client_api=tv_client_api,
        vacancies_parser=vacancies_parser,
    )


VacanciesServiceDep = Annotated[
    VacanciesService, Depends(get_vacancies_service)
]

