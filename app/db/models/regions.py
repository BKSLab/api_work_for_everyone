from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Region(Base):
    """
    Модель для хранения информации о регионах,
    """

    __tablename__ = 'regions'

    id: Mapped[int] = mapped_column(primary_key=True)
    region_name: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        unique=True,
        nullable=False,
        doc='Название региона.'
    )
    region_code_tv: Mapped[str] = mapped_column(
        String(length=10),
        unique=True,
        nullable=False,
        doc='Код региона для сайта Работа России.'
    )
    region_code_hh: Mapped[str] = mapped_column(
        String(length=10),
        nullable=False,
        doc='Код региона для сайта hh.ru.'
    )
    federal_district_code: Mapped[str] = mapped_column(
        String(length=10),
        nullable=False,
        doc='Код федерального округа.'
    )

    def __repr__(self) -> str:
        return (
            f'<Region(name={self.region_name}, '
            f'code_tv={self.region_code_tv}, '
            f'code_hh={self.region_code_hh})>'
        )
