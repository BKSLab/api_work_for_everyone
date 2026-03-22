from fastapi import status


class VacancyAiAssistantError(Exception):
    """Общая ошибка при работе AI ассистента."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, error_details: str):
        self.error_details = error_details
        super().__init__(self.error_details)

    def __str__(self) -> str:
        return f"Ошибка в работе AI ассистента. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return f"Ошибка в работе AI ассистента. Подробности: {self.error_details}"
