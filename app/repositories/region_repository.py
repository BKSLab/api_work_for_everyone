from sqlalchemy import insert, Result, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.models.regions import Region
from core.config_logger import logger


class RegionRepository:
    """Клас для взаимодействия с БД, для работы с регионами."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_region_all_data(self) -> list[Region] | None:
        """Метод запроса данных о регионах в таблицу."""
        try:
            data = select(Region)
            result: Result = await self.db_session.execute(statement=data)
            regions: list[Region] = result.scalars().all()
            return regions
        except SQLAlchemyError as error:
            logger.error(
                f"Database error while querying regions table: {error}"
            )
            return None
        except Exception as error:
            logger.exception(
                f"Unexpected error while querying regions table: {error}"
            )
            return None

    async def add_region_data(self, region_data: list[dict]) -> None:
        """Метод сохранения данных о регионе."""
        try:
            data = insert(table=Region).values(region_data)
            await self.db_session.execute(statement=data)
            await self.db_session.commit()
        except SQLAlchemyError as error:
            await self.db_session.rollback()
            logger.error(
                f'Database error while inserting region data: {error}'
            )
        except Exception as error:
            await self.db_session.rollback()
            logger.exception(
                f'Unexpected error while inserting region data: {error}'
            )

    async def get_region_data(self):
        """Метод получения списка всех регионов."""
        pass
