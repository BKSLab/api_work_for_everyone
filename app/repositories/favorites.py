import logging
from pprint import pformat

from sqlalchemy import Result, func, insert, select, update
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
                error_details="Ошибка при добавлении вакансии в избранное."
            ) from error

    async def delete_vacancy(self, vacancy_id: str, user_id: str) -> bool:
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
                    "⚠️ Попытка удаления несуществующей вакансии из избранного. "
                    "ID вакансии: %s, ID пользователя: %s", vacancy_id, user_id
                )
                return False

            await self.db_session.delete(favorite_entry)
            await self.db_session.commit()
            logger.info(
                "🗑️ Вакансия успешно удалена из избранного. "
                "ID вакансии: %s, ID пользователя: %s", vacancy_id, user_id
            )
            return True

        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise FavoritesRepositoryError(
                error_details=(
                    f"Ошибка при удалении вакансии из избранного. "
                    f"ID вакансии: {vacancy_id}, ID пользователя: {user_id}."
                )
            ) from error

    async def update_vacancy(self, vacancy_id: str, user_id: str, data: dict) -> None:
        """Обновляет данные вакансии в избранном и проставляет updated_at."""
        try:
            stmt = (
                update(FavoriteVacancies)
                .where(
                    FavoriteVacancies.vacancy_id == vacancy_id,
                    FavoriteVacancies.user_id == user_id,
                )
                .values(**data, updated_at=func.now())
            )
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            raise FavoritesRepositoryError(
                error_details=f"Ошибка при обновлении вакансии в избранном. ID вакансии: {vacancy_id}."
            ) from error

    async def get_count_favorites_vacancies(self, user_id: str) -> int:
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
                    f"Ошибка при подсчёте избранных вакансий. ID пользователя: {user_id}."
                )
            ) from error

    async def get_favorites_vacancies(self, user_id: str, page: int, page_size: int) -> list[FavoriteVacancies]:
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
                    f"Ошибка при получении списка избранных вакансий. "
                    f"ID пользователя: {user_id}, страница: {page}."
                )
            ) from error

    async def get_vacancy_by_id(self, vacancy_id: str, user_id: str | None) -> FavoriteVacancies | None:
        """Возвращает любую запись из избранного по vacancy_id (без привязки к пользователю)."""
        try:
            if user_id:
                stmt = (
                    select(FavoriteVacancies)
                    .where(
                        FavoriteVacancies.vacancy_id == vacancy_id,
                        FavoriteVacancies.user_id == user_id
                    )
                    .limit(1)
                )
            else:
                stmt = (
                    select(FavoriteVacancies)
                    .where(FavoriteVacancies.vacancy_id == vacancy_id)
                    .limit(1)
                )
            result: Result = await self.db_session.execute(statement=stmt)
            return result.scalar_one_or_none()
        except (SQLAlchemyError, Exception) as error:
            raise FavoritesRepositoryError(
                error_details=f"Ошибка при получении вакансии из избранного. ID вакансии: {vacancy_id}."
            ) from error

    async def get_favorite_vacancy_ids(
        self,
        user_id: str,
        vacancy_ids: list[str],
    ) -> set[str]:
        """
        Возвращает множество vacancy_id из переданного списка,
        которые находятся в избранном у пользователя.
        Один SELECT с IN-фильтром — O(n) по индексу.
        """
        if not vacancy_ids:
            return set()

        try:
            stmt = (
                select(
                    FavoriteVacancies.vacancy_id
                ).where(
                    FavoriteVacancies.user_id == user_id,
                    FavoriteVacancies.vacancy_id.in_(vacancy_ids),
                )
            )
            result: Result = await self.db_session.execute(statement=stmt)
            vacancies: list[FavoriteVacancies] = result.scalars().all()
            return set(vacancies)

        except (SQLAlchemyError, Exception) as error:
            raise FavoritesRepositoryError(
                error_details=(
                    f"Ошибка при получении ID избранных вакансий. ID пользователя: {user_id}."
                )
            ) from error
