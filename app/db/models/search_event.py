from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SearchEvent(Base):
    """
    Модель для хранения событий поиска вакансий.
    Одна запись = один вызов POST /vacancies/search.
    """

    __tablename__ = 'search_events'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        comment='Уникальный идентификатор события поиска.'
    )
    location: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
        comment='Населённый пункт, по которому выполнялся поиск.'
    )
    region_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        comment='Полное название региона.'
    )
    region_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment='Код региона по классификатору trudvsem.ru.'
    )
    count_hh: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment='Количество вакансий, полученных из hh.ru.'
    )
    count_tv: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment='Количество вакансий, полученных из trudvsem.ru.'
    )
    total_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment='Общее количество сохранённых вакансий.'
    )
    error_hh: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment='Флаг ошибки при запросе к hh.ru.'
    )
    error_tv: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment='Флаг ошибки при запросе к trudvsem.ru.'
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment='Дата и время события поиска.'
    )

    def __repr__(self) -> str:
        return (
            f"<SearchEvent(id={self.id}, location='{self.location}', "
            f"total={self.total_count}, created_at='{self.created_at}')>"
        )
