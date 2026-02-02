from sqlalchemy import Result, delete, func, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.vacancies import Vacancies
from exceptions.repositories import VacanciesRepositoryError


class VacanciesRepository:
    """Репозиторий для работы с вакансиями в базе данных."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def delete_vacancies_by_location(self, location: str) -> None:
        """Удаляет все вакансии в указанном населенном пункте."""
        try:
            stmt = delete(Vacancies).where(Vacancies.location == location)
            await self.db_session.execute(statement=stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise VacanciesRepositoryError(
                error_details=f"Error deleting vacancies. Location: {location}."
            ) from error

    async def save_vacancies(self, vacancies: list[dict]) -> None:
        """Сохраняет список вакансий в базе данных."""
        try:
            stmt = insert(table=Vacancies).values(vacancies)
            await self.db_session.execute(statement=stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise VacanciesRepositoryError(
                error_details="Error saving vacancies."
            ) from error

    async def get_vacancies(self, location: str, page: int, page_size: int) -> list[Vacancies]:
        """Возвращает список вакансий в указанном населенном пункте."""
        try:
            stmt = (
                select(Vacancies)
                .where(Vacancies.location == location)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result: Result = await self.db_session.execute(statement=stmt)
            vacancies: list[Vacancies] = result.scalars().all()
            return vacancies
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"Error retrieving vacancies. Location: {location}."
            ) from error

    async def get_vacancy_by_id(self, vacancy_id: str) -> Vacancies | None:
        """Возвращает вакансию по vacancy_id."""
        try:
            stmt = (
                select(Vacancies)
                .where(Vacancies.vacancy_id == vacancy_id)
            )
            result: Result = await self.db_session.execute(statement=stmt)
            vacancy: Vacancies | None = result.scalars().one_or_none()
            return vacancy
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"[get_vacancy_by_id]: Error retrieving vacancy. VacancyID: {vacancy_id}."
            ) from error

    async def get_count_vacancies(self, location: str) -> int:
        """Возвращает количество вакансий в указанном населенном пункте."""
        try:
            stmt = select(func.count()).select_from(Vacancies).where(
                Vacancies.location == location
            )
            result: Result = await self.db_session.execute(statement=stmt)
            count: int = result.scalar_one()
            return count
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"Error counting vacancies. Location: {location}."
            ) from error
