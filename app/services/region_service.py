from exceptions.repository_exceptions import RegionRepositoryError
from exceptions.service_exceptions import (
    RegionDataLoadError,
    RegionNotFoundError,
    RegionServiceError,
)
from schemas.region import RegionSchema
from utils.management_save_data_regions import read_csv_file_with_data_regions
from repositories.region_repository import RegionRepository
from core.config_logger import logger
from db.models.regions import Region


class RegionService:
    """Сервис для работы с регионами, используя репозиторий."""

    EXPECTED_REGIONS_COUNT = 85

    def __init__(self, region_repository: RegionRepository):
        self.region_repository = region_repository

    async def check_region_data(self, region_data: list[Region]) -> bool:
        """"Проверка результатов запроса данных о регионах."""
        if not region_data or len(region_data) != self.EXPECTED_REGIONS_COUNT:
            logger.error(
                'Data verification failed: either no data or incorrect '
                f'number of regions. Expected: {self.EXPECTED_REGIONS_COUNT}, '
                f'got: {len(region_data) if region_data else 0}'
            )
            return False
        return True

    async def is_region_data_present(self) -> None:
        """Проверка наличия и корректности данных о регионах в БД."""
        try:
            region_data = await self.region_repository.get_region_all_data()
            check_result = await self.check_region_data(
                region_data=region_data
            )
            if not check_result:
                raise RegionNotFoundError(
                    'data on regions is missing or their number does '
                    'not correspond to the expected'
                )
        except RegionRepositoryError as error:
            raise RegionServiceError from error

    async def get_region_list(self) -> list[RegionSchema]:
        """Получение списка регионов."""
        try:
            region_data = await self.region_repository.get_region_all_data()
            return [
                RegionSchema.model_validate(region) for region in region_data
            ]
        except RegionRepositoryError as error:
            raise RegionNotFoundError from error

    async def get_region_in_federal_district(
        self, federal_district_code: str
    ) -> list[RegionSchema]:
        """Получение списка регионов с разбивкой по федеральным округам."""
        try:
            region_data = await self.region_repository.get_region_all_in_fed_dist(
                fd_code=federal_district_code
            )
            if not region_data:
                raise RegionNotFoundError(
                    'No regions found in the federal district '
                    f'with code: {federal_district_code}'
                )
            return [RegionSchema.model_validate(region) for region in region_data]
        except RegionRepositoryError as error:
            raise RegionNotFoundError from error

    async def get_federal_districts_list(self) -> list[dict]:
        """Получение списка федеральных округов."""
        return [
            {
                'federal_district_name': 'Центральный федеральный округ',
                'federal_district_code': '30'
            },
            {
                'federal_district_name': 'Северо-Западный федеральный округ',
                'federal_district_code': '31'
            },
            {
                'federal_district_name': 'Приволжский федеральный округ',
                'federal_district_code': '33'
            },
            {
                'federal_district_name': 'Уральский федеральный округ',
                'federal_district_code': '34'
            },
            {
                'federal_district_name': 'Северо-Кавказский федеральный округ',
                'federal_district_code': '38'
            },
            {
                'federal_district_name': 'Южный федеральный округ',
                'federal_district_code': '40'
            },
            {
                'federal_district_name': 'Сибирский федеральный округ',
                'federal_district_code': '41'
            },
            {
                'federal_district_name': 'Дальневосточный федеральный округ',
                'federal_district_code': '42'
            },
        ]

    async def preload_region_data(self) -> None:
        """
        Загрузка данных о регионах в БД, если на момент старта приложения
        данные о регионах отсутствуют.
        """
        try:
            await self.is_region_data_present()
            logger.info('Region data already present in the database.')
            return
        except RegionNotFoundError as error:
            logger.info(
                f'No valid region data found. Message: {error}\n'
                'Starting preload...'
            )
        
            data_regions = read_csv_file_with_data_regions()
            if not data_regions:
                raise RegionDataLoadError(
                    'No region data found in CSV file'
                )
            await self.region_repository.add_region_data(
                region_data=data_regions
            )
            try:
                await self.is_region_data_present()
                logger.info(
                    'Region data preloaded and validated successfully.'
                )

            except RegionNotFoundError as error:
                raise RegionDataLoadError(
                    'Preloaded region data is invalid.'
                ) from error
        except (
            RegionServiceError, RegionRepositoryError, Exception
        ) as error:
            raise RegionDataLoadError(f'Unexpected error: {error}') from error
