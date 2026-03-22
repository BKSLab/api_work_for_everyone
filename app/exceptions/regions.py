from fastapi import status


class LocationValidationError(Exception):
    """Ошибка валидации населённого пункта."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, location: str, error_details: str):
        self.location = location
        self.error_details = error_details
        super().__init__(self.location, self.error_details)

    def __str__(self) -> str:
        return f"Ошибка валидации населённого пункта. Название: '{self.location}'. Подробности: {self.error_details}"

    @property
    def detail(self) -> str:
        return (
            f"Некорректное название населённого пункта: '{self.location}'. "
            f"Название должно быть на русском языке и не содержать цифр."
        )


class RegionNotFoundError(Exception):
    """
    Исключение для класса RegionService при
    отсутствии данных о регионе в БД.
    """
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, region_code: str):
        self.region_code = region_code
        super().__init__(self.region_code)

    def __str__(self) -> str:
        return f"Регион не найден. Код региона: '{self.region_code}'."

    @property
    def detail(self) -> str:
        return (
            f"Регион с кодом '{self.region_code}' не найден. "
            "Проверьте корректность кода."
        )


class RegionsByFDNotFoundError(Exception):
    """
    Исключение для класса RegionService при
    отсутствии данных о регионах в заданном федеральном округе.
    """
    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, federal_district_code: str):
        self.federal_district_code = federal_district_code
        super().__init__(self.federal_district_code)

    def __str__(self) -> str:
        return f"Регионы федерального округа не найдены. Код ФО: '{self.federal_district_code}'."

    @property
    def detail(self) -> str:
        return f"Регионы в федеральном округе с кодом '{self.federal_district_code}' не найдены."


class RegionDataLoadError(Exception):
    """Исключение для ошибок загрузки данных регионов"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    @property
    def detail(self) -> str:
        return f"Ошибка загрузки данных регионов. Подробности: {self.message}"
