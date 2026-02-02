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
            "Vacancy parsing error occurred while processing vacancy data. "
            f"Source: {self.source}. "
            f"Vacancy ID: {self.vacancy_id}. "
            f"Employer code: {self.employer_code}. "
            f"Error details: {self.error_details}"
        )

    @property
    def detail(self) -> str:
        return (
            f"An error occurred while processing vacancy data from the source '{self.source}'. "
            f"Details: {self.error_details}."
        )
