from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BlockedToken(Base):
    """Модель для хранения заблокированных JWT токенов."""

    __tablename__ = "blocked_tokens"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    jti: Mapped[str] = mapped_column(
        String, nullable=False, index=True, unique=True,
        doc='Уникальный идентификатор токена.'
    )
    exp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        doc='Время истечения срока действия токена.'
    )

    def __repr__(self) -> str:
        return f"<BlockedToken(jti={self.jti})>"
