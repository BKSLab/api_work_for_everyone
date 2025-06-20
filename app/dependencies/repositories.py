from fastapi import Depends
from typing import Annotated

from repositories.region_repository import RegionRepository
from dependencies.db_session import DbSessionDep


def get_region_repository(session: DbSessionDep) -> RegionRepository:
    return RegionRepository(session)


RegionRepositoryDep = Annotated[RegionRepository, Depends(get_region_repository)]
