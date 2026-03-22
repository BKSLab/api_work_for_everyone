from fastapi import status


class RegionRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с регионами."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в RegionRepository. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка базы данных при обработке данных регионов. Подробности: {self.error_details}"


class VacanciesRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с вакансиями."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в VacanciesRepository. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка базы данных при обработке данных вакансий. Подробности: {self.error_details}"


class FavoritesRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с избранным."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в FavoritesRepository. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка базы данных при обработке данных избранного. Подробности: {self.error_details}"


class AssistantSessionRepositoryError(Exception):
    """Исключение для класса репозитория для работы с сессиями AI-ассистента."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в AssistantSessionRepository. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка базы данных при сохранении сессии AI-ассистента. Подробности: {self.error_details}"


class ApiKeyRepositoryError(Exception):
    """Исключение для класса репозитория для работы с API-ключами."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в ApiKeyRepository. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка базы данных при обработке данных API-ключей. Подробности: {self.error_details}"
