from fastapi import APIRouter

from .endpoints import federal_districts, regions

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
