from fastapi import APIRouter
from .endpoints import regions, federal_districts

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
