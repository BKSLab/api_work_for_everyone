from fastapi import APIRouter

from schemas.region import FederalDistrictSchema
from dependencies.services import RegionServiceDep


router = APIRouter()


@router.get(
    path='/get-all',
    summary='Получить список всех федеральных округов.',
    description='Возвращает полный список всех федеральных округов.',
    response_model=list[FederalDistrictSchema]
)
async def list_federal_districts(
    region_service: RegionServiceDep
) -> list[FederalDistrictSchema]:
    """Возвращает полный список всех федеральных округов."""
    return await region_service.get_federal_districts_list()
