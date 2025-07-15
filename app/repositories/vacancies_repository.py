from sqlalchemy import Result, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.regions import Region
from exceptions.repository_exceptions import RegionRepositoryError


class VacanciesRepository:
    """Клас для взаимодействия с БД, для работы с вакансиями."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
