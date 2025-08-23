from fastapi import APIRouter

from .endpoints import (
    federal_districts,
    regions,
    vacancies,
)

router = APIRouter()

router.include_router(
    regions.router,
    prefix='/regions',
    tags=['Regions']
)


router.include_router(
    federal_districts.router,
    prefix='/federal-districts',
    tags=['Federal districts']
)


router.include_router(
    vacancies.router,
    prefix='/vacancies',
    tags=['Vacancies']
)
