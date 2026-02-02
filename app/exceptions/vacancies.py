from pprint import pformat
from fastapi import status


class VacanciesNotFoundError(Exception):
    """Вакансий по заданному коду региона и локации не найдено."""

    def __init__(self, region_code: str, location: str, source: str):
        self.region_code = region_code
        self.location = location
        self.source = source
        super().__init__(self.region_code, self.location, self.source)

    def __str__(self):
        return (
            f"VacanciesNotFoundError: No vacancies found for region_code='{self.region_code}', "
            f"location='{self.location}' in source='{self.source}'."
        )
        
    @property
    def detail(self) -> str:
        return (
            f"No vacancies found in the specified area using source '{self.source}'. "
            f"Region: {self.region_code}, Location: {self.location}."
        )


class VacancyNotFoundError(Exception):
    """Вакансия не найдена в БД."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, vacancy_id: str, error_details: str):
        self.vacancy_id = vacancy_id
        self.error_details = error_details
        super().__init__(self.vacancy_id, self.error_details)

    def __str__(self) -> str:
        return f"VacancyNotFoundError: No vacancy found for vacancy_id='{self.vacancy_id}'. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return (
            f"No vacancy found for the provided ID '{self.vacancy_id}'. Please check the ID and try again. "
            f"Details: {self.error_details}"
        )


class VacancyAlreadyInFavoritesError(Exception):
    """Исключение для дублирования вакансии в избранном."""
    status_code = status_code = status.HTTP_409_CONFLICT

    def __init__(self, favorite_data: dict):
        self.favorite_data = favorite_data
        super().__init__(self.favorite_data)

    def __str__(self) -> str:
        return (
            "An attempt to add a vacancy that the user has previously "
            f"added to favorites. favorite_data:={pformat(self.favorite_data)}"
        )

    @property
    def detail(self) -> str:
        return "This vacancy is already in favorites for user."
