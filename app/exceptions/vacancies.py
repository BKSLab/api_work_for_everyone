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
            f"Вакансии не найдены. Код региона: '{self.region_code}', "
            f"населённый пункт: '{self.location}', источник: '{self.source}'."
        )

    @property
    def detail(self) -> str:
        return (
            f"Вакансии не найдены в указанном районе (источник: '{self.source}'). "
            f"Регион: {self.region_code}, населённый пункт: {self.location}."
        )


class VacancyNotFoundError(Exception):
    """Вакансия не найдена в БД."""
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, vacancy_id: str, error_details: str = ""):
        self.vacancy_id = vacancy_id
        self.error_details = error_details
        super().__init__(self.vacancy_id, self.error_details)

    def __str__(self) -> str:
        return f"Вакансия не найдена. ID вакансии: '{self.vacancy_id}'. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Вакансия с ID '{self.vacancy_id}' не найдена. Проверьте корректность ID."


class VacancyAlreadyInFavoritesError(Exception):
    """Исключение для дублирования вакансии в избранном."""
    status_code = status.HTTP_409_CONFLICT

    def __init__(self, favorite_data: dict):
        self.favorite_data = favorite_data
        super().__init__(self.favorite_data)

    def __str__(self) -> str:
        return (
            "Попытка добавить вакансию, которая уже добавлена в избранное. "
            f"Данные: {pformat(self.favorite_data)}"
        )

    @property
    def detail(self) -> str:
        return "Данная вакансия уже добавлена в избранное."
