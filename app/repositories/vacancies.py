import logging

from sqlalchemy import Result, delete, func, insert, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.vacancies import Vacancies
from exceptions.repositories import VacanciesRepositoryError

logger = logging.getLogger(__name__)


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
                error_details=f"Ошибка при удалении вакансий. Населённый пункт: {location}."
            ) from error

    SAVE_BATCH_SIZE = 1000

    async def save_vacancies(self, vacancies: list[dict]) -> None:
        """Сохраняет список вакансий в базе данных."""
        total = len(vacancies)
        total_batches = (total + self.SAVE_BATCH_SIZE - 1) // self.SAVE_BATCH_SIZE
        logger.info("💾 Начало сохранения вакансий. Всего: %d, батчей: %d.", total, total_batches)

        try:
            for i in range(0, total, self.SAVE_BATCH_SIZE):
                batch = vacancies[i:i + self.SAVE_BATCH_SIZE]
                batch_num = i // self.SAVE_BATCH_SIZE + 1
                logger.info(
                    "💾 Батч #%d/%d: сохраняем вакансии %d–%d.",
                    batch_num, total_batches, i + 1, i + len(batch),
                )
                try:
                    stmt = insert(table=Vacancies).values(batch)
                    await self.db_session.execute(statement=stmt)
                except (SQLAlchemyError, Exception) as error:
                    await self.db_session.rollback()
                    logger.error(
                        "❌ Ошибка в батче #%d/%d (вакансии %d–%d). Детали: %s",
                        batch_num, total_batches, i + 1, i + len(batch), error, exc_info=True,
                    )
                    raise VacanciesRepositoryError(
                        error_details=f"Ошибка при сохранении батча #{batch_num}."
                    ) from error

            await self.db_session.commit()
            logger.info("✅ Вакансии сохранены. Всего записей: %d.", total)

        except VacanciesRepositoryError:
            raise
        except (SQLAlchemyError, Exception) as error:
            await self.db_session.rollback()
            logger.error(
                "❌ Ошибка при коммите. Всего вакансий: %d. Детали: %s",
                total, error, exc_info=True,
            )
            raise VacanciesRepositoryError(
                error_details="Ошибка при сохранении вакансий."
            ) from error

    async def get_vacancies(
        self,
        location: str,
        page: int,
        page_size: int,
        keyword: str | None = None,
        source: str | None = None,
    ) -> list[Vacancies]:
        """Возвращает список вакансий в указанном населенном пункте."""
        try:
            stmt = select(Vacancies).where(Vacancies.location == location)
            if source:
                stmt = stmt.where(Vacancies.vacancy_source == source)
            if keyword:
                stmt = stmt.where(
                    or_(
                        Vacancies.vacancy_name.ilike(f"%{keyword}%"),
                        Vacancies.description.ilike(f"%{keyword}%"),
                    )
                )
            stmt = stmt.offset((page - 1) * page_size).limit(page_size)
            result: Result = await self.db_session.execute(statement=stmt)
            vacancies: list[Vacancies] = result.scalars().all()
            return vacancies
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"Ошибка при получении вакансий. Населённый пункт: {location}."
            ) from error

    async def get_vacancy_by_id(self, vacancy_id: str) -> Vacancies | None:
        """Возвращает вакансию по vacancy_id."""
        try:
            stmt = (
                select(Vacancies)
                .where(Vacancies.vacancy_id == vacancy_id)
            )
            result: Result = await self.db_session.execute(statement=stmt)
            vacancies = result.scalars().all()

            if not vacancies:
                return None

            if len(vacancies) > 1:
                logger.warning(
                    "⚠️ Найдено несколько вакансий с vacancy_id=%s. "
                    "Количество: %s. Возвращается первая запись.",
                    vacancy_id, len(vacancies)
                )

            return vacancies[0]
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"Ошибка при получении вакансии. ID вакансии: {vacancy_id}."
            ) from error

    async def get_count_vacancies(
        self,
        location: str,
        keyword: str | None = None,
        source: str | None = None,
    ) -> int:
        """Возвращает количество вакансий в указанном населенном пункте."""
        try:
            stmt = select(func.count()).select_from(Vacancies).where(
                Vacancies.location == location
            )
            if source:
                stmt = stmt.where(Vacancies.vacancy_source == source)
            if keyword:
                stmt = stmt.where(
                    or_(
                        Vacancies.vacancy_name.ilike(f"%{keyword}%"),
                        Vacancies.description.ilike(f"%{keyword}%"),
                    )
                )
            result: Result = await self.db_session.execute(statement=stmt)
            count: int = result.scalar_one()
            return count
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"Ошибка при подсчёте вакансий. Населённый пункт: {location}."
            ) from error

    async def get_count_vacancies_by_source(
        self,
        location: str,
        keyword: str | None = None,
        source: str | None = None,
    ) -> dict[str, int]:
        """Возвращает количество вакансий по источникам с учётом фильтров."""
        try:
            stmt = (
                select(Vacancies.vacancy_source, func.count())
                .where(Vacancies.location == location)
            )
            if source:
                stmt = stmt.where(Vacancies.vacancy_source == source)
            if keyword:
                stmt = stmt.where(
                    or_(
                        Vacancies.vacancy_name.ilike(f"%{keyword}%"),
                        Vacancies.description.ilike(f"%{keyword}%"),
                    )
                )
            stmt = stmt.group_by(Vacancies.vacancy_source)
            result: Result = await self.db_session.execute(statement=stmt)
            return {row[0]: row[1] for row in result.all()}
        except (SQLAlchemyError, Exception) as error:
            raise VacanciesRepositoryError(
                error_details=f"Ошибка при подсчёте вакансий по источникам. Населённый пункт: {location}."
            ) from error
