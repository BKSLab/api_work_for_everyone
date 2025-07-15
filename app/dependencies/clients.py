from typing import Annotated

from fastapi import Depends

from clients.hh_api_client import HHClient
from clients.tv_api_client import TVClient
from dependencies.http_client import HTTPClientDep


def get_hh_client(httpx_client: HTTPClientDep) -> HHClient:
    return HHClient(httpx_client=httpx_client)


def get_tv_client(httpx_client: HTTPClientDep) -> TVClient:
    return TVClient(httpx_client=httpx_client)


HHClientDep = Annotated[
    HHClient, Depends(get_hh_client)
]

TVClientDep = Annotated[
    TVClient, Depends(get_tv_client)
]
