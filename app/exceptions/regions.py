from fastapi import status


class LocationValidationError(Exception):
    """Ошибка валидации населённого пункта."""
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, location: str, error_details: str):
        self.location = location
        self.error_details = error_details
        super().__init__(self.location, self.error_details)

    def __str__(self) -> str:
        return f"LocationValidationError: Invalid location name '{self.location}'. Details: {self.error_details}"

    @property
    def detail(self) -> str:
        return (
            f"Invalid location name provided: '{self.location}'. The name must be in Russian and contain no numbers. "
            f"Details: {self.error_details}"
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
        return f"RegionNotFoundError: No region data found for code '{self.region_code}'."
    
    @property
    def detail(self) -> str:
        return (
            f"No region found for the provided code '{self.region_code}'. "
            "Please check the code's correctness."
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
        return f"RegionsByFDNotFoundError: No regions found for federal district code '{self.federal_district_code}'."

    @property
    def detail(self) -> str:
        return f"No regions found for the federal district with code '{self.federal_district_code}'."


class RegionDataLoadError(Exception):
    """Исключение для ошибок загрузки данных регионов"""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    @property
    def detail(self) -> str:
        return f"Failed to load region data. Details: {self.message}"
