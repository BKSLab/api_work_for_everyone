from fastapi import status


class VacanciesServiceError(Exception):
    """Общий класс исключений для VacanciesService."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the Vacancies service. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"An error occurred while processing vacancies. Details: {self.error_details}"


class RegionServiceError(Exception):
    """Общее исключение для класса RegionService."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the Regions service. Details: {self.error_details}"
    
    @property
    def detail(self) -> str:
        return f"An error occurred while processing region data. Details: {self.error_details}"


class UsersServiceError(Exception):
    """Общий класс исключений для сервиса работы с пользователями."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the Users service. Details: {self.error_details}"
    
    @property
    def detail(self) -> str:
        return f"An error occurred while processing user data. Details: {self.error_details}"


class BlocklistServiceError(Exception):
    """Класс исключений для сервиса работы с черным списком токенов."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the Blocklist service. Details: {self.error_details}"
    
    @property
    def detail(self) -> str:
        return f"An error occurred in the blocklist service. Details: {self.error_details}"
