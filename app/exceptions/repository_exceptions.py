from fastapi import status


class RegionRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с регионами."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, *, cause: Exception = None):
        self.__cause__ = cause
        super().__init__()

    def detail(self) -> str:
        return (
            'An error occurred while retrieving region. Please contact '
            'the developer or try again after some time.'
        )


class VacanciesRepositoryError(Exception):
    """Исключение для класса репозиттория для работы с вакансиями."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, *, cause: Exception = None):
        self.__cause__ = cause
        super().__init__()

    def detail(self) -> str:
        return (
            'An error occurred while processing vacancies. '
            'Please contact the developer or try again later.'
        )


class UsersRepositoryError(Exception):
    """Базовое исключение для ошибок репозитория Users."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, *, cause: Exception = None):
        self.__cause__ = cause
        super().__init__()

    def detail(self) -> str:
        return (
            'An error occurred while processing users. '
            'Please contact the developer or try again later.'
        )
