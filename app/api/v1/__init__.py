from fastapi import APIRouter, Depends

from dependencies.api_key import verify_api_key

from .endpoints import (
    api_keys,
    favorites,
    federal_districts,
    regions,
    vacancies,
    vacancy_assistant,
)

router = APIRouter()

# Этот эндпоинт использует собственную аутентификацию по мастер-ключу
router.include_router(
    api_keys.router,
    prefix="/api-keys",
    tags=['api_keys'],
)

router.include_router(
    regions.router,
    prefix='/regions',
    tags=['Regions'],
    dependencies=[Depends(verify_api_key)],
)


router.include_router(
    federal_districts.router,
    prefix='/federal-districts',
    tags=['Federal districts'],
    dependencies=[Depends(verify_api_key)],
)


router.include_router(
    vacancies.router,
    prefix='/vacancies',
    tags=['Vacancies'],
    dependencies=[Depends(verify_api_key)],
)


router.include_router(
    favorites.router,
    prefix='/favorites',
    tags=['Favorites'],
    dependencies=[Depends(verify_api_key)],
)


router.include_router(
    vacancy_assistant.router,
    prefix='/assistant',
    tags=['Assistant'],
    dependencies=[Depends(verify_api_key)],
)
