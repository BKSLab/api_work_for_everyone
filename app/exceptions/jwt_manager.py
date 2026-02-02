from pprint import pformat

from starlette import status


class JWTManagerError(Exception):
    """Общий класс исключений для JWT менеджера."""
    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, error_details: str, message: str):
        self.error_details = error_details
        self.message = message
        super().__init__(self.error_details, self.message)

    def __str__(self) -> str:
        return f"JWTManagerError: {self.message}. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Authorization error: {self.message}."
