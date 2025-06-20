from sqlalchemy import Result, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.regions import Region
from exceptions.repository_exceptions import RegionRepositoryError


class RegionRepository:
    """Клас для взаимодействия с БД, для работы с регионами."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_region_all_data(self) -> list[Region]:
        """Возвращает полный список регионов."""
        try:
            data = select(Region)
            result: Result = await self.db_session.execute(statement=data)
            regions: list[Region] = result.scalars().all()
            return regions
        except SQLAlchemyError as error:
            raise RegionRepositoryError from error
        except Exception as error:
            raise RegionRepositoryError from error

    async def get_region_all_in_fed_dist(self, fd_code) -> list[Region]:
        """Возвращает список регионов в федеральном округе."""
        try:
            data = select(Region).where(
                Region.federal_district_code == fd_code
            )
            result: Result = await self.db_session.execute(statement=data)
            regions: list[Region] = result.scalars().all()
            return regions
        except SQLAlchemyError as error:
            raise RegionRepositoryError from error
        except Exception as error:
            raise RegionRepositoryError from error

    async def add_region_data(self, region_data: list[dict]) -> None:
        """Сохраняет данные о регионах при старте приложения."""
        try:
            data = insert(table=Region).values(region_data)
            await self.db_session.execute(statement=data)
            await self.db_session.commit()
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            raise RegionRepositoryError from error
        except Exception as error:
            await self.db_session.rollback()
            raise RegionRepositoryError from error
