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
from schemas.region import FederalDistrictSchema, RegionSchema, RegionSchemaDb

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
                "❌ Проверка данных регионов не пройдена: нет данных или неверное количество записей. "
                "Ожидалось: %s, получено: %s",
                self.EXPECTED_REGIONS_COUNT, len(region_data) if region_data else 0
            )
            return False
        return True

    async def _check_federal_districts_data(self, federal_districts_data: list[Region]) -> bool:
        """Проверяет, что список федеральных округов не пуст и содержит ожидаемое количество записей."""
        if not federal_districts_data or len(federal_districts_data) != self.EXPECTED_FD_COUNT:
            logger.error(
                "❌ Проверка данных федеральных округов не пройдена: нет данных или неверное количество записей. "
                "Ожидалось: %s, получено: %s",
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
            raise RegionDataLoadError(message="Файл с данными регионов не найден.")

        try:

            with open(self.REGIONS_FILE, "r", encoding="utf-8") as f:
                regions_data = json.load(f)
            return regions_data

        except json.JSONDecodeError as error:
            raise RegionDataLoadError(message="Ошибка декодирования JSON-файла регионов.") from error
        except IOError as error:
            raise RegionDataLoadError("Ошибка чтения файла данных регионов.") from error

    def _read_file_data_federal_districts(self) -> list[dict]:
        """Читает и возвращает данные о федеральных округах из JSON-файла."""
        if not self.FEDERAL_DISTRICTS_FILE.exists():
            raise RegionDataLoadError(message="Файл с данными федеральных округов не найден.")

        try:

            with open(self.FEDERAL_DISTRICTS_FILE, "r", encoding="utf-8") as f:
                federal_districts_data = json.load(f)
            return federal_districts_data

        except json.JSONDecodeError as error:
            raise RegionDataLoadError(message="Ошибка декодирования JSON-файла федеральных округов.") from error
        except IOError as error:
            raise RegionDataLoadError("Ошибка чтения файла данных федеральных округов.") from error

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
                error_details="Ошибка валидации данных при получении списка регионов."
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
                error_details="Ошибка валидации данных при получении регионов федерального округа."
            ) from error

    async def get_region_by_code(self, region_code_tv: str) -> dict:
        """
        Возвращает данные региона по его коду.

        Args:
            region_code_tv: Код региона.

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
            logger.error("❌ Регион не найден в базе данных. Код региона: %s", region_code_tv)
            raise RegionNotFoundError(region_code=region_code_tv)

        try:
            return RegionSchemaDb.model_validate(region_data_raw).model_dump()
        except ValidationError as error:
            raise RegionServiceError(
                error_details="Ошибка валидации данных региона."
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
                error_details="Ошибка валидации данных при получении списка федеральных округов."
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
        if await self._is_region_data_present():
            logger.info("✅ Данные регионов уже загружены в базу данных.")
            return

        region_data = self._read_file_data_regions()
        await self.region_repository.add_regions_data(region_data=region_data)

        if not await self._is_region_data_present():
            raise RegionDataLoadError(
                message="Не удалось загрузить данные регионов в базу данных."
            )
        logger.info("✅ Данные регионов успешно загружены в базу данных.")

    async def _preload_federal_districts_data(self) -> None:
        """
        Выполняет предварительную загрузку данных о федеральных округах в БД.

        Проверяет, есть ли данные в базе. Если их нет, читает данные
        из локального JSON-файла и сохраняет их в базу данных.
        Если после сохранения данные все еще отсутствуют, выбрасывает исключение.

        Raises:
            RegionDataLoadError: Если не удалось загрузить данные в базу данных.
        """
        if await self._is_federal_districts_data_present():
            logger.info("✅ Данные федеральных округов уже загружены в базу данных.")
            return

        federal_districts_data = self._read_file_data_federal_districts()
        await self.region_repository.add_federal_districts_data(
            federal_districts_data=federal_districts_data
        )

        if not await self._is_federal_districts_data_present():
            raise RegionDataLoadError(
                message="Не удалось загрузить данные федеральных округов в базу данных."
            )
        logger.info("✅ Данные федеральных округов успешно загружены в базу данных.")

    async def initialize_region_data(self) -> None:
        """Параллельная проверка и предварительная загрузка данных о регионах и федеральных округах."""
        logger.info("🚀 Запуск проверки и загрузки данных регионов и федеральных округов...")

        # Запускаем задачи последовательно, чтобы избежать состояния гонки в сессии БД
        await self._preload_region_data()
        await self._preload_federal_districts_data()
