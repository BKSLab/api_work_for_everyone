from pprint import pformat

from fastapi import status


class HHAPIRequestError(Exception):
    """Ошибка при обращении к API 'hh.ru'."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str, request_url: str, request_params: dict = {}):
        self.error_details = error_details
        self.request_params = request_params
        self.request_url = request_url
        super().__init__(self.error_details, self.request_params, self.request_url)

    def __str__(self) -> str:
        return (
            f"Ошибка запроса к API hh.ru. URL: {self.request_url}. "
            f"Параметры: {pformat(self.request_params)}. Подробности: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return f"Ошибка при запросе к API hh.ru. Подробности: {self.error_details}"


class TVAPIRequestError(Exception):
    """Ошибка при обращении к API 'trudvsem.ru'."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str, request_url: str, request_params: dict = {}):
        self.error_details = error_details
        self.request_params = request_params
        self.request_url = request_url
        super().__init__(self.error_details, self.request_params, self.request_url)

    def __str__(self) -> str:
        return (
            f"Ошибка запроса к API trudvsem.ru. URL: {self.request_url}. "
            f"Параметры: {pformat(self.request_params)}. Подробности: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return f"Ошибка при запросе к API trudvsem.ru. Подробности: {self.error_details}"
