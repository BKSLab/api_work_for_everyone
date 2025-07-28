from sqlalchemy import Result, insert, select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.config_logger import logger
from db.models.vacancies import Vacancies
from exceptions.repository_exceptions import VacanciesRepositoryError


class VacanciesRepository:
    """Клас для взаимодействия с БД, для работы с вакансиями."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def delete_vacancies_by_location(self, location: str) -> None:
        """
        Удаляет все вакансии, связанные с заданным населенным пунктом.
        """
        try:
            stmt = delete(Vacancies).where(Vacancies.location == location)
            await self.db_session.execute(statement=stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(f'Ошибка при удалении вакансий по локации "{location}": {error}')
            raise VacanciesRepositoryError(cause=error) from error

    async def save_vacancies(self, vacancies: list[dict]) -> None:
        """Сохраняет данные о вакансиях."""
        try:
            stmt = insert(table=Vacancies).values(vacancies)
            await self.db_session.execute(statement=stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(f'Ошибка при сохранении данных о вакансиях: {error}')
            raise VacanciesRepositoryError(cause=error) from error
