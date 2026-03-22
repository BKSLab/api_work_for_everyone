import logging
from typing import Annotated

from fastapi import Depends, Header, HTTPException

from db.models.api_keys import ApiKey
from dependencies.services import ApiKeyServiceDep
from exceptions.api_keys import (
    ExpiredApiKeyError,
    InactiveApiKeyError,
    InvalidApiKeyError,
)

logger = logging.getLogger(__name__)


async def verify_api_key(
    api_key: Annotated[str, Header(alias="X-API-Key")],
    api_key_service: ApiKeyServiceDep,
) -> ApiKey:
    """Проверяет API-ключ из заголовка X-API-Key."""
    try:
        return await api_key_service.validate_api_key(api_key)
    except (InvalidApiKeyError, ExpiredApiKeyError, InactiveApiKeyError) as e:
        logger.warning("⚠️ Ошибка валидации API-ключа: %s", e.detail)
        raise HTTPException(status_code=e.status_code, detail=e.detail)


VerifyApiKeyDep = Annotated[ApiKey, Depends(verify_api_key)]
