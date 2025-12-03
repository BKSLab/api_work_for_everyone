from fastapi import status


class EmptyRegionsDatabaseError(Exception):
    """Вызывается, когда в БД отсутствуют записи о регионах (таблица пуста)."""
    def __init__(self):
        super().__init__(
            'data on regions is missing or their number does '
            'not correspond to the expected'
        )


class RegionStartupError(Exception):
    """
    Общее исключение при инициализации данных о регионах
    во время запуска приложения.
    """


class RegionNotFoundError(Exception):
    """
    Исключение для класса RegionService при
    отсутствии данных о регионе в БД.
    """
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, region_code: str):
        self.region_code = region_code

    def detail(self) -> str:
        return (
            'Could not find region data for the received '
            f'code: {self.region_code}. Check the correctness '
            'of the region code.'
        )


class RegionsNotFoundError(Exception):
    """
    Исключение для класса RegionService при
    отсутствии данных о регионах в заданном федеральном округе.
    """
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, federal_district_code: str):
        self.federal_district_code = federal_district_code

    def detail(self) -> str:
        return (
            'No regions found in the federal district '
            f'with code: {self.federal_district_code}'
        )


class RegionDataLoadError(Exception):
    """Исключение для ошибок загрузки данных регионов"""
    pass


class InvalidLocationError(Exception):
    """Ошибка валидации населённого пункта."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, location: str):
        self.location = location

    def detail(self) -> str:
        return f'Invalid location: {self.location}'


class TVAPIRequestError(Exception):
    """Ошибка при обращении к API 'Работа для всех'."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, request_params: dict):
        self.request_params = request_params

    def detail(self) -> str:
        return (
            'Failed to get a response from "Work for Everyone" API. '
            f'Request parameters: {self.request_params}'
        )


class HHAPIRequestError(Exception):
    """Ошибка при обращении к API 'hh.ru'."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, request_params: dict):
        self.request_params = request_params

    def detail(self) -> str:
        return (
            'Failed to get a response from "hh.ru" API. '
            f'Request parameters: {self.request_params}'
        )


class VacanciesTVNotFoundError(Exception):
    """Вакансийц по заданному коду региона не найдено. API 'Работа для всех'."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, region_code: str, location: str):
        self.region_code = region_code
        self.location = location

    def detail(self) -> str:
        return (
            'No vacancies found in the specified region using the trudvsem API. '
            f'Region code: {self.region_code}, location: {self.location}'
        )


class VacancyTVNotFoundError(Exception):
    """Не удалось получить детальную информацию по вакансии. API 'Работа для всех'."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, vacancy_id: str, employer_code: str):
        self.vacancy_id = vacancy_id
        self.employer_code = employer_code

    def detail(self) -> str:
        return (
            'No vacancy found using the trudvsem API. '
            f'vacancy_id: {self.vacancy_id}, employer_code: {self.employer_code}'
        )


class VacanciesHHNotFoundError(Exception):
    """Вакансийц по заданному коду региона не найдено. API 'Работа для всех'."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, region_code: str, location: str):
        self.region_code = region_code
        self.location = location

    def detail(self) -> str:
        return (
            'No vacancies found in the specified region using the hh.ru API. '
            f'Region code: {self.region_code}, location: {self.location}'
        )


class VacancyHHNotFoundError(Exception):
    """Вакансия на сайте hh.ru не найдена по заданному id."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, vacancy_id: str):
        self.vacancy_id = vacancy_id

    def detail(self) -> str:
        return (
            'No vacancy found using the hh.ru API. '
            f'vacancy_id: {self.vacancy_id}'
        )


class VacanciesNotFoundError(Exception):
    """Вакансий по заданной локации не найдено."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, location: str):
        self.location = location

    def detail(self) -> str:
        return (
            f'No vacancies found for location "{self.location}". '
            'Please check the spelling and try again.'
        )


class VacancyNotFoundError(Exception):
    """Вакансия не найдена в БД."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, vacancy_id: str):
        self.vacancy_id = vacancy_id

    def detail(self) -> str:
        return (
            f'No vacancy found for vacancy_id "{self.vacancy_id}". '
            'Please check the spelling and try again.'
        )


class VacancyParseError(Exception):
    """Ошибка при разборе вакансий от Trudvsem"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def detail(self) -> str:
        return (
            'An error occurred while processing vacancy data received from the "Work for Everyone" API. '
            'Please try again later or contact support.'
        )

