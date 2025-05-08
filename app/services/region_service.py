from exceptions.custom_exceptions import RegionDataLoadError
from utils.management_save_data_regions import read_csv_file_with_data_regions
from repositories.region_repository import RegionRepository
from core.config_logger import logger
from db.models.regions import Region


class RegionService:
    """Сервис для работы с регионами, используя репозиторий."""

    def __init__(self, region_repository: RegionRepository):
        self.region_repository = region_repository

    async def check_region_data(selfm, region_data: list[Region]) -> bool:
        """"Проверка результатов запроса данных о регионах."""
        if not region_data or len(region_data) != 85:
            logger.error(
                'Data verification failed: '
                'either no data or incorrect number of regions.'
            )
            return False
        return True
    
    async def is_region_data_present(self) -> bool:
        """Проверка наличия и корректности данных о регионах в БД."""
        region_data = await self.region_repository.get_region_all_data()
        return await self.check_region_data(region_data=region_data)

    async def preload_region_data_if_empty(self) -> None:
        """
        Загрузка данных о регионах в БД, если на момент старта приложения
        данные о регионах отсутствуют.
        """
        try:
            if await self.is_region_data_present():
                logger.info('Region data already present in the database.')
                return
            data_regions = read_csv_file_with_data_regions()
            if not data_regions:
                raise RegionDataLoadError('No region data found in CSV file')
            save_result = await self.region_repository.add_region_data(
                region_data=data_regions
            )
            if not save_result:
                raise RegionDataLoadError('Failed to save region data to database')
            if not await self.is_region_data_present():
                raise RegionDataLoadError('Data verification failed after saving')
        except Exception as e:
            raise RegionDataLoadError(f'Region data loading failed: {str(e)}')
