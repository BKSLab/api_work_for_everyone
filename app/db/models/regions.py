from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Region(Base):
    """
    Модель для хранения информации о регионах,
    """

    __tablename__ = 'regions'

    __table_args__ = ({
        'comment': 'Справочник регионов РФ'
    })

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        unique=True,
        nullable=False,
        doc='Название региона.',
        comment='Человекочитаемое название региона РФ'
    )
    code_tv: Mapped[str] = mapped_column(
        String(length=10),
        unique=True,
        nullable=False,
        doc='Код региона для сайта Работа России.',
        comment='Код региона на сайте "Работа России"'
    )
    code_hh: Mapped[str] = mapped_column(
        String(length=10),
        nullable=False,
        doc='Код региона для сайта hh.ru.',
        comment='Код региона на сайте hh.ru'
    )
    federal_district_code: Mapped[str] = mapped_column(
        String(length=10),
        nullable=False,
        doc='Код федерального округа.',
        comment='Код федерального округа, к которому относится регион'
    )

    def __repr__(self) -> str:
        return (
            f'<Region(name={self.name}, '
            f'code_tv={self.code_tv}, '
            f'code_hh={self.code_hh})>'
        )
