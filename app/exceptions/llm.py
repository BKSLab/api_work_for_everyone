from fastapi import status


class LlmClientRequestError(Exception):
    """Исключение при запросе к llm-proxy-service"""


class LlmClientContentError(Exception):
    """Исключение обработки ответа от llm-proxy-service"""


class LlmApiRequestError(Exception):
    """Ошибка при обращении к API 'trudvsem.ru'."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str, request_url: str):
        self.error_details = error_details
        self.request_url = request_url
        super().__init__(self.error_details, self.request_url)

    def __str__(self) -> str:
        return (
            f"Ошибка запроса к LLM API. URL: {self.request_url}. "
            f"Подробности: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return f"Ошибка при запросе к LLM API. Подробности: {self.error_details}"
