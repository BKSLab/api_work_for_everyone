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
            f"API request to 'hh.ru' failed. URL: {self.request_url}. "
            f"Params: {pformat(self.request_params)}. Details: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return f"An error occurred while requesting the 'hh.ru' API. Details: {self.error_details}"


class TVAPIRequestError(Exception):
    """Ошибка при обращении к API 'Работа для всех'."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str, request_url: str, request_params: dict = {}):
        self.error_details = error_details
        self.request_params = request_params
        self.request_url = request_url
        super().__init__(self.error_details, self.request_params, self.request_url)
    
    def __str__(self) -> str:
        return (
            f"API request to 'trudvsem.ru' failed. URL: {self.request_url}. "
            f"Params: {pformat(self.request_params)}. Details: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return f"An error occurred while requesting the 'trudvsem.ru' API. Details: {self.error_details}"
