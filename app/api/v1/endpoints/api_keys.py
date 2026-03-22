from typing import Annotated, List

from fastapi import APIRouter, Body, Header, HTTPException, status

from core.config_logger import logger
from dependencies.services import ApiKeyServiceDep
from exceptions.api_keys import ApiKeyNotFoundError, MasterApiKeyError
from exceptions.repositories import ApiKeyRepositoryError
from schemas.api_key import (
    ApiKeyCreate,
    ApiKeyDeactivateRequest,
    ApiKeyInfoResponse,
    ApiKeyResponse,
    ApiKeyStatusResponse,
)

router = APIRouter()


@router.get(
    path="/list",
    status_code=status.HTTP_200_OK,
    summary="Получение списка всех API ключей",
    description="Возвращает полный список всех созданных API ключей с их детальной информацией. **Требует валидного мастер-ключа.**",
    operation_id="getAllApiKeys",
    response_description="Список всех API ключей.",
    responses={
        200: {"description": "Успешный ответ со списком ключей."},
        403: {
            "description": "Неверный мастер-ключ.",
            "content": {"application/json": {"example": {"detail": "Invalid master API key provided."}}},
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {"application/json": {"example": {"detail": "A database error occurred."}}},
        },
    },
    response_model=List[ApiKeyInfoResponse],
)
async def get_all_keys(
    service: ApiKeyServiceDep,
    master_key: Annotated[str, Header(..., alias="X-Master-Key", description="Мастер-ключ для авторизации.")],
):
    """Возвращает список всех API ключей."""
    logger.info("🔑 Запрос GET /api-keys/list.")
    try:
        keys = await service.get_all_api_keys(master_key=master_key)
        logger.info("✅ Список API-ключей успешно получен. Количество: %d.", len(keys))
        return keys
    except (MasterApiKeyError, ApiKeyRepositoryError) as error:
        logger.exception("❌ Ошибка при получении списка API-ключей. Детали: %s", error)
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/create",
    status_code=status.HTTP_201_CREATED,
    summary="Создание нового API ключа",
    description="Создает новый API ключ для доступа к публичным эндпоинтам. **Требует валидного мастер-ключа.**",
    operation_id="createNewApiKey",
    response_description="API ключ успешно создан.",
    responses={
        201: {"description": "API ключ успешно создан."},
        403: {
            "description": "Неверный мастер-ключ.",
            "content": {"application/json": {"example": {"detail": "Invalid master API key provided."}}},
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {"application/json": {"example": {"detail": "A database error occurred while creating API key."}}},
        },
    },
    response_model=ApiKeyResponse,
)
async def create_new_api_key(
    service: ApiKeyServiceDep,
    api_key_data: Annotated[ApiKeyCreate, Body(description="Данные для создания нового API ключа.")],
    master_key: Annotated[str, Header(..., alias="X-Master-Key", description="Мастер-ключ для авторизации.")],
):
    """Создает новый API ключ на основе предоставленных данных."""
    logger.info("🔑 Запрос POST /api-keys/create. Получатель: '%s'.", api_key_data.issued_for)
    try:
        new_key = await service.create_api_key(api_key_data=api_key_data, master_key=master_key)
        logger.info("✅ API-ключ успешно создан. Префикс: %s.", new_key.api_key_prefix)
        return new_key
    except (MasterApiKeyError, ApiKeyRepositoryError) as error:
        logger.exception(
            "❌ Ошибка при создании API-ключа. Получатель: '%s'. Детали: %s",
            api_key_data.issued_for,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Деактивация существующего API ключа",
    description="Деактивирует ключ по его префиксу. **Требует валидного мастер-ключа.**",
    operation_id="deactivateApiKey",
    response_description="API ключ успешно деактивирован.",
    responses={
        200: {"description": "API ключ успешно деактивирован."},
        403: {
            "description": "Неверный мастер-ключ.",
            "content": {"application/json": {"example": {"detail": "Invalid master API key provided."}}},
        },
        404: {
            "description": "API ключ не найден.",
            "content": {"application/json": {"example": {"detail": "API key with prefix '...' not found."}}},
        },
        500: {
            "description": "Внутренняя ошибка сервера.",
            "content": {"application/json": {"example": {"detail": "A database error occurred."}}},
        },
    },
    response_model=ApiKeyStatusResponse,
)
async def deactivate_existing_api_key(
    service: ApiKeyServiceDep,
    deactivate_request: Annotated[ApiKeyDeactivateRequest, Body(description="Префикс API ключа для деактивации.")],
    master_key: Annotated[str, Header(..., alias="X-Master-Key", description="Мастер-ключ для авторизации.")],
):
    """Деактивирует API ключ на основе его префикса."""
    prefix = deactivate_request.api_key_prefix
    logger.info("🔑 Запрос POST /api-keys/deactivate. Префикс: %s.", prefix)
    try:
        result = await service.deactivate_api_key(api_key_prefix=prefix, master_key=master_key)
        logger.info("✅ API-ключ успешно деактивирован. Префикс: %s.", prefix)
        return result
    except (MasterApiKeyError, ApiKeyNotFoundError, ApiKeyRepositoryError) as error:
        logger.exception("❌ Ошибка при деактивации API-ключа. Префикс: '%s'. Детали: %s", prefix, error)
        raise HTTPException(status_code=error.status_code, detail=error.detail)
