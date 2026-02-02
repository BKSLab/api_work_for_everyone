from fastapi import status


class RegionRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с регионами."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the RegionRepository. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"A database error occurred while processing region data. Details: {self.error_details}"


class VacanciesRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с вакансиями."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the VacanciesRepository. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"A database error occurred while processing vacancies data. Details: {self.error_details}"


class FavoritesRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с избранным."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the FavoritesRepository. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"A database error occurred while processing favorites data. Details: {self.error_details}"


class UsersRepositoryError(Exception):
    """Базовое исключение для ошибок репозитория Users."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the UsersRepository. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"A database error occurred while processing user data. Details: {self.error_details}"


class BlocklistRepositoryError(Exception):
    """Базовое исключение для ошибок репозитория BlocklistRepository."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"An error occurred in the BlocklistRepository. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"A database error occurred while processing blocklist data. Details: {self.error_details}"
