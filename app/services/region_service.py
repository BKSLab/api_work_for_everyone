from core.config_logger import logger
from db.models.regions import Region
from exceptions.repository_exceptions import RegionRepositoryError
from exceptions.service_exceptions import (
    EmptyRegionsDatabaseError,
    RegionDataLoadError,
    RegionNotFoundError,
    RegionsNotFoundError,
    RegionStartupError,
)
from repositories.region_repository import RegionRepository
from schemas.region import RegionSchema
from utils.management_save_data_regions import read_csv_file_with_data_regions


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
            region_data = await self.region_repository.get_regions_all_data()
            check_result = await self.check_region_data(
                region_data=region_data
            )
            if not check_result:
                logger.warning('No valid region data found.')
                raise EmptyRegionsDatabaseError()
        except RegionRepositoryError as error:
            logger.error('Ошибка при обращении к БД:', exc_info=error)
            raise

    async def get_region_list(self) -> list[RegionSchema]:
        """Получение списка регионов."""
        try:
            region_data = await self.region_repository.get_regions_all_data()
            return [
                RegionSchema.model_validate(region) for region in region_data
            ]
        except RegionRepositoryError as error:
            logger.error('Ошибка при обращении к БД:', exc_info=error)
            raise

    async def get_region_in_federal_district(
        self, federal_district_code: str
    ) -> list[RegionSchema]:
        """Получение списка регионов с разбивкой по федеральным округам."""
        try:
            region_data = await self.region_repository.get_regions_all_in_fed_dist(
                fd_code=federal_district_code
            )
            if not region_data:
                logger.error(
                    f'No regions found with fede_code: {federal_district_code}'
                )
                raise RegionsNotFoundError(federal_district_code)
            return [
                RegionSchema.model_validate(region) for region in region_data
            ]
        except RegionRepositoryError as error:
            logger.error('Ошибка при обращении к БД:', exc_info=error)
            raise

    async def get_region_by_code(self, region_code_tv: str) -> dict:
        """
        Возвращает данные региона по государственному
        коду регионов (region_code_tv).
        """
        try:
            region_data = await self.region_repository.get_region_data(
                region_code_tv=region_code_tv
            )
            if not region_data:
                logger.error(f'No regions found with code: {region_code_tv}')
                raise RegionNotFoundError(region_code_tv)
            return RegionSchema.model_validate(region_data).model_dump()
        except RegionRepositoryError as error:
            logger.error('Ошибка при обращении к БД:', exc_info=error)
            raise

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
        except EmptyRegionsDatabaseError:
            try:
                data_regions = read_csv_file_with_data_regions()
                await self.region_repository.add_regions_data(
                    region_data=data_regions
                )
                await self.is_region_data_present()
                logger.info(
                    'Region data preloaded and validated successfully.'
                )
                return
            except (
                RegionDataLoadError,
                RegionRepositoryError,
                EmptyRegionsDatabaseError
            ) as error:
                logger.error(f'Ошибка при загрузке данных о регионах: {error}')
                raise RegionStartupError() from error
        except RegionRepositoryError as error:
            raise RegionStartupError() from error
