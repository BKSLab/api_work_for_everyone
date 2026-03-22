from fastapi import status


class VacanciesServiceError(Exception):
    """Общий класс исключений для VacanciesService."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в сервисе вакансий. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка при обработке вакансий. Подробности: {self.error_details}"


class RegionServiceError(Exception):
    """Общее исключение для класса RegionService."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в сервисе регионов. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка при обработке данных регионов. Подробности: {self.error_details}"


class ApiKeyServiceError(Exception):
    """Общий класс исключений для ApiKeyService."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в сервисе API-ключей. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка при обработке API-ключа. Подробности: {self.error_details}"
