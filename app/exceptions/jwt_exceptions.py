from starlette import status


class JWTManagerError(Exception):
    """Общий класс исключений для JWT менеджера."""
    status_code = status.HTTP_401_UNAUTHORIZED
    _base_detail = "Ошибка аутентификации"

    def __init__(self, message: str = ""):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def detail(self) -> str:
        if self.message:
            return f"{self._base_detail}: {self.message}"
        return self._base_detail
