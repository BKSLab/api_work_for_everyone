import logging
from pprint import pformat

from sqlalchemy import Result, func, insert, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.favorites import FavoriteVacancies
from exceptions.repositories import FavoritesRepositoryError
from exceptions.vacancies import VacancyAlreadyInFavoritesError

logger = logging.getLogger(__name__)


class FavoritesRepository:
    """Репозиторий для работы с избранными вакансиями в базе данных."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def add_vacancy(self, favorite_data: dict) -> bool:
        """Добавляет вакансию в избранное."""
        try:
            stmt = (
                insert(FavoriteVacancies)
                .values(favorite_data)
            )
            await self.db_session.execute(statement=stmt)
            await self.db_session.commit()    

        except IntegrityError as error:
            await self.db_session.rollback()
            raise VacancyAlreadyInFavoritesError(favorite_data=favorite_data) from error

        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise FavoritesRepositoryError(
                error_details=f"Error adding vacancy to favorites. Data: {pformat(favorite_data)}."
            ) from error

    async def delete_vacancy(self, vacancy_id: str, user_id: int) -> bool:
        """Удаляет вакансию из избранного и возвращает статус операции."""
        try:
            stmt = select(FavoriteVacancies).where(
                FavoriteVacancies.vacancy_id == vacancy_id,
                FavoriteVacancies.user_id == user_id
            )
            result = await self.db_session.execute(stmt)
            favorite_entry = result.scalar_one_or_none()

            if favorite_entry is None:
                logger.warning(
                    "Попытка удаления несуществующей избранной вакансии. "
                    "vacancy_id: %s, user_id: %s", vacancy_id, user_id
                )
                return False

            await self.db_session.delete(favorite_entry)
            await self.db_session.commit()
            logger.info(
                "Вакансия успешно удалена из избранного. "
                "vacancy_id: %s, user_id: %s", vacancy_id, user_id
            )
            return True

        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise FavoritesRepositoryError(
                error_details=(
                    f"Error deleting vacancy from favorites. "
                    f"VacancyID: {vacancy_id}, UserID: {user_id}."
                )
            ) from error

    async def get_count_favorites_vacancies(self, user_id: int) -> int:
        """Возвращает количество вакансий в избранном."""
        try:
            stmt = select(func.count()).select_from(FavoriteVacancies).where(
                FavoriteVacancies.user_id == user_id
            )
            result: Result = await self.db_session.execute(statement=stmt)
            count: int = result.scalar_one()
            return count
        except (SQLAlchemyError, Exception) as error:
            raise FavoritesRepositoryError(
                error_details=(
                    f"Error counting favorite vacancies. UserID: {user_id}."
                )
            ) from error

    async def get_favorites_vacancies(self, user_id: int, page: int, page_size: int) -> list[FavoriteVacancies]:
        """Возвращает список избранных вакансий пользователя."""
        try:
            stmt = (
                select(FavoriteVacancies)
                .where(FavoriteVacancies.user_id == user_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result: Result = await self.db_session.execute(statement=stmt)
            vacancies: list[FavoriteVacancies] = result.scalars().all()
            return vacancies
        except (SQLAlchemyError, Exception) as error:
            raise FavoritesRepositoryError(
                error_details=(
                    f"Error retrieving favorite vacancies. "
                    f"UserID: {user_id}, Page: {page}."
                )
            ) from error
