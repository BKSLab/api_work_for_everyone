from typing import Annotated

from fastapi import Depends

from dependencies.db_session import DbSessionDep
from repositories.region_repository import RegionRepository


def get_region_repository(session: DbSessionDep) -> RegionRepository:
    return RegionRepository(session)


RegionRepositoryDep = Annotated[RegionRepository, Depends(get_region_repository)]
