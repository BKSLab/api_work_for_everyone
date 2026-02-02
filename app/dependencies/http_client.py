from typing import Annotated, AsyncGenerator

import httpx
from fastapi import Depends


async def get_http_session() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Генератор для создания HTTP-сессии."""
    async with httpx.AsyncClient(timeout=60) as httpx_client:
        yield httpx_client


HTTPClientDep = Annotated[
    httpx.AsyncClient, Depends(get_http_session)
]
