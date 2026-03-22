from typing import Annotated

from fastapi import Depends

from clients.hh_api_client import HHClient
from clients.llm import LlmClient
from clients.tv_api_client import TVClient
from core.settings import get_settings
from dependencies.http_client import HTTPClientDep

settings = get_settings()


def get_hh_client(httpx_client: HTTPClientDep) -> HHClient:
    return HHClient(httpx_client=httpx_client)


def get_tv_client(httpx_client: HTTPClientDep) -> TVClient:
    return TVClient(httpx_client=httpx_client)


def get_llm_client(httpx_client: HTTPClientDep) -> LlmClient:
    return LlmClient(
        httpx_client= httpx_client,
        model=settings.llm.llm_model.get_secret_value(),
        url=settings.llm.llm_api_url.get_secret_value(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.llm.llm_api_key.get_secret_value()}",
        }
    )


HHClientDep = Annotated[
    HHClient, Depends(get_hh_client)
]


TVClientDep = Annotated[
    TVClient, Depends(get_tv_client)
]


LlmClientDep = Annotated[
    LlmClient, Depends(get_llm_client)
]
