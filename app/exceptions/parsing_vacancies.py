from fastapi import status


class VacancyParseError(Exception):
    """Ошибка при разборе вакансий от Trudvsem"""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str, vacancy_id: str, employer_code: str, source: str):
        self.error_details = error_details
        self.vacancy_id = vacancy_id
        self.employer_code = employer_code
        self.source = source
        super().__init__(self.error_details, self.vacancy_id, self.employer_code, self.source)

    def __str__(self) -> str:
        return (
            f"Ошибка разбора вакансии. Источник: {self.source}. "
            f"ID вакансии: {self.vacancy_id}. "
            f"Код работодателя: {self.employer_code}. "
            f"Подробности: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return (
            f"Ошибка при обработке данных вакансии из источника '{self.source}'. "
            f"Подробности: {self.error_details}."
        )
