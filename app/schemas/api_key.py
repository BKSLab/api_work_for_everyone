from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ApiKeyCreate(BaseModel):
    """Тело запроса для создания нового API-ключа."""

    issued_for: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Описание клиента или сервиса, для которого выдаётся ключ.",
        examples=["telegram_bot"],
    )
    owner_email: EmailStr = Field(
        ...,
        description="Контактный email владельца ключа.",
        examples=["user@example.com"],
    )
    comment: Optional[str] = Field(
        None,
        max_length=500,
        description="Произвольный комментарий для внутреннего использования.",
        examples=["Ключ для интеграции с системой аналитики."],
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Дата и время истечения срока действия ключа. Если не указано — ключ бессрочный.",
        examples=["2027-01-01T00:00:00"],
    )


class ApiKeyResponse(BaseModel):
    """Ответ при создании API-ключа. Содержит сам ключ — отображается только один раз."""

    model_config = ConfigDict(from_attributes=True)

    api_key: str = Field(
        ...,
        description="Сгенерированный API-ключ. Сохраните его — повторно получить невозможно.",
    )
    api_key_prefix: str = Field(..., description="Префикс ключа для идентификации в логах.")
    issued_for: str = Field(..., description="Назначение ключа.")
    owner_email: EmailStr = Field(..., description="Email владельца ключа.")
    comment: Optional[str] = Field(None, description="Комментарий.")
    created_at: datetime = Field(..., description="Дата и время создания ключа.")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения срока действия. None — бессрочный.")
    is_active: bool = Field(..., description="Статус активности ключа.")


class ApiKeyDeactivateRequest(BaseModel):
    """Тело запроса для деактивации API-ключа по его префиксу."""

    api_key_prefix: str = Field(
        ...,
        min_length=12,
        max_length=16,
        description="Префикс API-ключа для деактивации.",
        examples=["wfe_a1b2c3d4"],
    )


class ApiKeyStatusResponse(BaseModel):
    """Ответ с актуальным статусом активности API-ключа."""

    model_config = ConfigDict(from_attributes=True)

    api_key_prefix: str = Field(..., description="Префикс API-ключа.")
    is_active: bool = Field(..., description="Текущий статус активности: True — активен, False — деактивирован.")


class ApiKeyInfoResponse(BaseModel):
    """Полная безопасная информация об API-ключе (без хешированного значения)."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Уникальный идентификатор записи в БД.")
    api_key_prefix: str = Field(..., description="Префикс ключа для идентификации.")
    issued_for: str = Field(..., description="Назначение ключа.")
    owner_email: EmailStr = Field(..., description="Email владельца ключа.")
    comment: Optional[str] = Field(None, description="Комментарий.")
    created_at: datetime = Field(..., description="Дата и время создания ключа.")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения срока действия. None — бессрочный.")
    is_active: bool = Field(..., description="Статус активности ключа.")
