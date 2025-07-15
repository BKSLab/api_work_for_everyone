import re

from clients.hh_api_client import HHClient
from clients.tv_api_client import TVClient
from core.config_logger import logger
from exceptions.repository_exceptions import RegionRepositoryError
from exceptions.service_exceptions import InvalidLocationError, RegionNotFoundError
from repositories.vacancies_repository import VacanciesRepository
from services.region_service import RegionService


class VacanciesService:
    """
    Сервис для работы с вакансиями. Загрузка,
    подготовка данных и сохранение вакансий в БД.
    """

    def __init__(
        self,
        region_service: RegionService,
        vacancies_repository: VacanciesRepository,
        hh_client_api: HHClient,
        tv_client_api: TVClient,
    ):
        self.region_service = region_service
        self.vacancies_repository = vacancies_repository
        self.hh_client_api = hh_client_api
        self.tv_client_api = tv_client_api

    async def normalize_location(self, parts: list[str], hyphen: bool) -> str:
        """Нормализует наименование населённого пункта."""
        return (
            '-'.join(part.capitalize() for part in parts)
            if hyphen else
            ' '.join(part.capitalize() for part in parts)
        )

    async def location_validation(self, location: str) -> str:
        """Валидирует наименование населенного пункта."""
        if '-' in location:
            split_location = location.split('-')
            hyphen = True
        else:
            split_location = location.split()
            hyphen = False
        if (
            len(split_location) <= 3
            and all(
                symbol.isspace() or symbol.isalpha()
                for symbol in (part_name for part_name in split_location)
            )
            and re.search(r'^[А-Яа-яЁё\s\-]+\Z', location)
        ):
            return await self.normalize_location(
                parts=split_location, hyphen=hyphen
            )
        logger.warning(f'Invalid location: {location}')
        raise InvalidLocationError(location)

    async def validation_and_get_region_data(
        self, location: str, region_code: str
    ) -> dict:
        """
        Валидация наименование населенного пункта и получение данных региона
        для подготовки запроса на поиск вакансий.
        """
        logger.info(
            'Данные, полученные на валидацию:'
            f'\n - region_code: {region_code}\n = location: {location}'
        )
        try:
            return {
                'location': await self.location_validation(
                    location=location
                ),
                'region_data': await self.region_service.get_region_by_code(
                    region_code_tv=region_code
                )
            }
        except (
            RegionNotFoundError,
            RegionRepositoryError,
            InvalidLocationError
        ):
            raise

    async def get_vacancies_count(self, location: str, region_data: dict) -> dict:
        """
        Получает количество вакансий по заданному региону и населенному
        пункту.
        """
        logger.info(
            'Данные, полученные на получение количества вакансий:'
            f'\n - location: {location}\n - region_data: {region_data}'
        )
