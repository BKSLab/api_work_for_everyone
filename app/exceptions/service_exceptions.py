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
