from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FederalDistricts(Base):
    """
    Модель для хранения информации о федеральных округах,
    """

    __tablename__ = 'federal_districts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(
        String(length=100),
        unique=True,
        nullable=False,
        doc='Наименование федерального округа.'
    )
    code: Mapped[str] = mapped_column(
        String(length=10),
        nullable=False,
        doc='Код федерального округа.'
    )

    def __repr__(self) -> str:
        return f"<FederalDistricts(name={self.name}, code={self.code})>"
