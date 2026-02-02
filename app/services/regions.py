import asyncio
import json
import logging
from pathlib import Path

from pydantic import ValidationError

from db.models.regions import Region
from exceptions.regions import (
    RegionDataLoadError,
    RegionNotFoundError,
    RegionsByFDNotFoundError,
)
from exceptions.services import RegionServiceError
from repositories.regions import RegionRepository
from schemas.region import FederalDistrictSchema, RegionSchema

logger = logging.getLogger(__name__)


class RegionService:
    """Сервис для работы с данными о регионах."""

    EXPECTED_REGIONS_COUNT = 85
    EXPECTED_FD_COUNT = 8
    REGIONS_FILE = Path(__file__).parent.parent / "utils" / "data_region" / "regions.json"
    FEDERAL_DISTRICTS_FILE = Path(__file__).parent.parent / "utils" / "data_region" / "federal_districts.json"

    def __init__(self, region_repository: RegionRepository):
        self.region_repository = region_repository

    async def _check_region_data(self, region_data: list[Region]) -> bool:
        """Проверяет, что список регионов не пуст и содержит ожидаемое количество записей."""
        if not region_data or len(region_data) != self.EXPECTED_REGIONS_COUNT:
            logger.error(
                "Data verification failed: either no data or incorrect "
                "number of regions. Expected: %s, got: %s",
                self.EXPECTED_REGIONS_COUNT, len(region_data) if region_data else 0
            )
            return False
        return True

    async def _check_federal_districts_data(self, federal_districts_data: list[Region]) -> bool:
        """Проверяет, что список федеральных округов не пуст и содержит ожидаемое количество записей."""
        if not federal_districts_data or len(federal_districts_data) != self.EXPECTED_FD_COUNT:
            logger.info(
                "Data verification failed: either no data or incorrect "
                "number of federal districts. Expected: %s, got: %s",
                self.EXPECTED_FD_COUNT, len(federal_districts_data) if federal_districts_data else 0
            )
            return False
        return True

    async def _is_region_data_present(self) -> bool:
        """Проверяет наличие и корректность данных о регионах в базе данных."""
        region_data = await self.region_repository.get_regions_all_data()
        return await self._check_region_data(region_data=region_data)

    async def _is_federal_districts_data_present(self) -> bool:
        """Проверяет наличие и корректность данных о федеральных округах в базе данных."""
        federal_districts_data = await self.region_repository.get_federal_districts_all_data()
        return await self._check_federal_districts_data(
            federal_districts_data=federal_districts_data
        )

    def _read_file_data_regions(self) -> list[dict]:
        """Читает и возвращает данные о регионах из JSON-файла."""
        if not self.REGIONS_FILE.exists():
            raise RegionDataLoadError(message="Regions data file not found.")

        try:

            with open(self.REGIONS_FILE, "r", encoding="utf-8") as f:
                regions_data = json.load(f)
            return regions_data

        except json.JSONDecodeError as error:
            raise RegionDataLoadError(message="Error decoding regions JSON data.") from error
        except IOError as error:
            raise RegionDataLoadError("Error reading regions data file.") from error

    def _read_file_data_federal_districts(self) -> list[dict]:
        """Читает и возвращает данные о федеральных округах из JSON-файла."""
        if not self.FEDERAL_DISTRICTS_FILE.exists():
            raise RegionDataLoadError(message="Federal_districts data file not found.")

        try:

            with open(self.FEDERAL_DISTRICTS_FILE, "r", encoding="utf-8") as f:
                federal_districts_data = json.load(f)
            return federal_districts_data

        except json.JSONDecodeError as error:
            raise RegionDataLoadError(message="Error decoding federal districts JSON data.") from error
        except IOError as error:
            raise RegionDataLoadError("Error reading federal districts data file.") from error

    async def get_region_list(self) -> list[RegionSchema]:
        """
        Возвращает полный список всех регионов.

        Returns:
            Список объектов `RegionSchema`, представляющих все регионы.

        Raises:
            RegionServiceError: В случае ошибки валидации данных.
        """
        region_data = await self.region_repository.get_regions_all_data()
        try:
            return [
                RegionSchema.model_validate(region) for region in region_data
            ]
        except ValidationError as error:
            raise RegionServiceError(
                error_details="An error occurred during data validation for the region list."
            ) from error

    async def get_region_in_federal_district(
        self, federal_district_code: str
    ) -> list[RegionSchema]:
        """
        Возвращает список регионов в указанном федеральном округе.

        Args:
            federal_district_code: Код федерального округа.

        Returns:
            Список объектов `RegionSchema`, отфильтрованных по федеральному округу.

        Raises:
            RegionsByFDNotFoundError: Если регионы для данного округа не найдены.
            RegionServiceError: В случае ошибки валидации данных.
        """
        region_data = await self.region_repository.get_regions_all_in_fed_dist(
            fd_code=federal_district_code
        )
        if not region_data:
            raise RegionsByFDNotFoundError(federal_district_code=federal_district_code)

        try:
            return [
                RegionSchema.model_validate(region) for region in region_data
            ]
        except ValidationError as error:
            raise RegionServiceError(
                error_details="An error occurred during data validation for regions in the federal district."
            ) from error

    async def get_region_by_code(self, region_code_tv: str) -> dict:
        """
        Возвращает данные региона по его коду "Работа России".

        Args:
            region_code_tv: Код региона, используемый на портале "Работа России".

        Returns:
            Словарь с данными региона.

        Raises:
            RegionNotFoundError: Если регион с указанным кодом не найден.
            RegionServiceError: В случае ошибки валидации данных.
        """
        region_data_raw = await self.region_repository.get_region_data(
            region_code_tv=region_code_tv
        )
        if not region_data_raw:
            logger.error("Не удалось найти данные по региону с region_code_tv=%s", region_code_tv)
            raise RegionNotFoundError(region_code=region_code_tv)
        
        try:
            return RegionSchema.model_validate(region_data_raw).model_dump()
        except ValidationError as error:
            raise RegionServiceError(
                error_details="An error occurred during data validation for the specified region."
            ) from error

    async def get_federal_districts_list(self) -> list[FederalDistrictSchema]:
        """
        Возвращает полный список всех федеральных округов.

        Returns:
            Список объектов `FederalDistrictSchema`, представляющих все регионы.

        Raises:
            RegionServiceError: В случае ошибки валидации данных.
        """
        federal_districts_data = await self.region_repository.get_federal_districts_all_data()
        try:
            return [
                FederalDistrictSchema.model_validate(federal_district) for federal_district in federal_districts_data
            ]
        except ValidationError as error:
            raise RegionServiceError(
                error_details="An error occurred during data validation for the federal district list."
            ) from error

    async def _preload_region_data(self) -> None:
        """
        Выполняет предварительную загрузку данных о регионах в БД.

        Проверяет, есть ли данные в базе. Если их нет, читает данные
        из локального JSON-файла и сохраняет их в базу данных.
        Если после сохранения данные все еще отсутствуют, выбрасывает исключение.

        Raises:
            RegionDataLoadError: Если не удалось загрузить данные в базу данных.
        """
        # Проверка наличия данных о регионах в БД
        if await self._is_region_data_present():
            logger.info("Region data already present in the database.")
            return
        
        # Если данных нет, попытка их загрузки из json файла
        region_data = self._read_file_data_regions()
        
        # Попытка записи данных в БД
        await self.region_repository.add_regions_data(region_data=region_data)
        
        # Повторная проверка наличия данных о регионах в БД
        if not await self._is_region_data_present():
            raise RegionDataLoadError(
                message="Failed to load region data into the database."
            )
        logger.info("Region data successfully loaded into the database.")

    async def _preload_federal_districts_data(self) -> None:
        """
        Выполняет предварительную загрузку данных о федеральных округах в БД.

        Проверяет, есть ли данные в базе. Если их нет, читает данные
        из локального JSON-файла и сохраняет их в базу данных.
        Если после сохранения данные все еще отсутствуют, выбрасывает исключение.

        Raises:
            RegionDataLoadError: Если не удалось загрузить данные в базу данных.
        """
        # Проверка наличия данных о федеральных округах в БД
        if await self._is_federal_districts_data_present():
            logger.info("federal districts data already present in the database.")
            return
        
        # Если данных нет, попытка их загрузки из json файла
        federal_districts_data = self._read_file_data_federal_districts()
        
        # Попытка записи данных в БД
        await self.region_repository.add_federal_districts_data(
            federal_districts_data=federal_districts_data
        )
        
        # Повторная проверка наличия данных о федеральных округах в БД
        if not await self._is_federal_districts_data_present():
            raise RegionDataLoadError(
                message="Failed to load federal districts data into the database."
            )
        logger.info("Federal districts data successfully loaded into the database.")

    async def initialize_region_data(self) -> None:
        """Параллельная проверка и предварительная загрузка данных о регионах и федеральных округах."""
        logger.info(
            ">>> Start parallel check and loading of data for regions and federal districts..."
        )

        # Запускаем задачи последовательно, чтобы избежать состояния гонки в сессии БД
        await self._preload_region_data()
        await self._preload_federal_districts_data()
