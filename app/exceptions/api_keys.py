from fastapi import status


class InvalidApiKeyError(Exception):
    """Ключ не найден или невалиден."""
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "API-ключ отсутствует или недействителен."

    def __init__(self, error_details: str = "Ключ не прошёл проверку."):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Невалидный API-ключ: {self.error_details}"


class MasterApiKeyError(Exception):
    """Мастер-ключ невалиден."""
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Неверный мастер-ключ."

    def __init__(self, error_details: str = "Мастер-ключ не совпадает с настроенным."):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка мастер-ключа: {self.error_details}"


class ApiKeyNotFoundError(Exception):
    """API ключ не найден."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, api_key_prefix: str):
        self.api_key_prefix = api_key_prefix
        super().__init__(self.api_key_prefix)

    def __str__(self) -> str:
        return f"API-ключ с префиксом '{self.api_key_prefix}' не найден в базе данных."

    @property
    def detail(self) -> str:
        return f"API-ключ с префиксом '{self.api_key_prefix}' не найден."


class ExpiredApiKeyError(Exception):
    """Ключ просрочен."""
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, api_key_prefix: str):
        self.api_key_prefix = api_key_prefix
        super().__init__(self.api_key_prefix)

    def __str__(self) -> str:
        return f"API-ключ с префиксом '{self.api_key_prefix}' истёк."

    @property
    def detail(self) -> str:
        return f"API-ключ с префиксом '{self.api_key_prefix}' истёк."


class InactiveApiKeyError(Exception):
    """Ключ деактивирован."""
    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, api_key_prefix: str):
        self.api_key_prefix = api_key_prefix
        super().__init__(self.api_key_prefix)

    def __str__(self) -> str:
        return f"API-ключ с префиксом '{self.api_key_prefix}' деактивирован."

    @property
    def detail(self) -> str:
        return f"API-ключ с префиксом '{self.api_key_prefix}' деактивирован."
