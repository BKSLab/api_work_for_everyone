import logging

from sqlalchemy import Result, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.federal_districts import FederalDistricts
from db.models.regions import Region
from exceptions.repositories import RegionRepositoryError


logger = logging.getLogger(__name__)


class RegionRepository:
    """Репозиторий для работы с регионами в базе данных."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_regions_all_data(self) -> list[Region]:
        """Возвращает полный список регионов."""
        try:
            data = select(Region)
            result: Result = await self.db_session.execute(statement=data)
            regions: list[Region] = result.scalars().all()
            return regions
        except (SQLAlchemyError, Exception) as error:
            raise RegionRepositoryError(
                error_details="Error retrieving all regions."
            ) from error

    async def get_federal_districts_all_data(self) -> list[Region]:
        """Возвращает полный список федеральных округов."""
        try:
            data = select(FederalDistricts)
            result: Result = await self.db_session.execute(statement=data)
            regions: list[FederalDistricts] = result.scalars().all()
            return regions
        except (SQLAlchemyError, Exception) as error:
            raise RegionRepositoryError(
                error_details="Error retrieving all federal_districts."
            ) from error

    async def get_regions_all_in_fed_dist(self, fd_code: str) -> list[Region]:
        """Возвращает список регионов в федеральном округе."""
        try:
            data = select(Region).where(
                Region.federal_district_code == fd_code
            )
            result: Result = await self.db_session.execute(statement=data)
            regions: list[Region] = result.scalars().all()
            return regions
        except (SQLAlchemyError, Exception) as error:
            raise RegionRepositoryError(
                error_details=(
                    f"Error retrieving regions by federal district. "
                    f"FD_Code: {fd_code}."
                )
            ) from error

    async def get_region_data(self, region_code_tv) -> Region | None:
        """Возвращает данные одного региона."""
        try:
            data = select(Region).where(
                Region.code_tv == region_code_tv
            )
            result: Result = await self.db_session.execute(statement=data)
            regions: Region = result.scalars().one_or_none()
            return regions
        except (SQLAlchemyError, Exception) as error:
            raise RegionRepositoryError(
                error_details=f"Error retrieving region data. RegionCodeTV: {region_code_tv}."
            ) from error

    async def add_regions_data(self, region_data: list[dict]) -> None:
        """Сохраняет данные о регионах при старте приложения."""
        try:
            data = insert(table=Region).values(region_data)
            await self.db_session.execute(statement=data)
            await self.db_session.commit()
            logger.info("Сохранено %d регионов.", len(region_data))
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise RegionRepositoryError(
                error_details="Error adding new regions to the database."
            ) from error

    async def add_federal_districts_data(self, federal_districts_data: list[dict]) -> None:
        """Сохраняет данные о федеральных округах при старте приложения."""
        try:
            data = insert(table=FederalDistricts).values(federal_districts_data)
            await self.db_session.execute(statement=data)
            await self.db_session.commit()
            logger.info("Сохранено %d федеральных округов.", len(federal_districts_data))
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise RegionRepositoryError(
                error_details="Error adding new federal districts to the database."
            ) from error
