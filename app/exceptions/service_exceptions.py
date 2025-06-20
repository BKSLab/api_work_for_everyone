class RegionServiceError(Exception):
    """
    Исключение для класса RegionService при возникновении
    общих ошибок в работе методов класса и вызываемых сущностей.
    """
    pass


class RegionNotFoundError(Exception):
    """
    Исключение для класса RegionService при
    отсутствии данных о регионе в БД.
    """
    pass


class RegionDataLoadError(Exception):
    """Исключение для ошибок загрузки данных регионов"""
    pass
