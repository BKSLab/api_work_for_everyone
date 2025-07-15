import httpx


class HHClient:
    """Клас для взаимодействия API hh.ru для загрузки вакансий."""

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client
