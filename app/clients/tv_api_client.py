import httpx


class TVClient:
    """Клас для взаимодействия API trudvsem.ru для загрузки вакансий."""

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client
