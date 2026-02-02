import asyncio
import logging
import re
from pprint import pformat

from pydantic import ValidationError

from clients.hh_api_client import HHClient
from clients.tv_api_client import TVClient
from db.models.favorites import FavoriteVacancies
from db.models.vacancies import Vacancies
from exceptions.api_clients import HHAPIRequestError, TVAPIRequestError
from exceptions.parsing_vacancies import VacancyParseError
from exceptions.regions import LocationValidationError
from exceptions.services import VacanciesServiceError
from exceptions.vacancies import (
    VacanciesNotFoundError,
    VacancyNotFoundError,
)
from repositories.favorites import FavoritesRepository
from repositories.vacancies import VacanciesRepository
from schemas.vacancies import (
    FavoriteVacanciesListSchema,
    VacanciesListSchema,
    VacancyDetailsOutSchema,
    VacancyOutSchema,
)
from services.parsing_vacancies import VacanciesParsingService
from services.regions import RegionService

logger = logging.getLogger(__name__)


class VacanciesService:
    """Сервис для управления бизнес-логикой, связанной с вакансиями."""
    MAX_COUNT_PARTS_IN_LOCATION = 3
    FLAG_VACANCY_NOT_FOUND = "not_found"
    SEMAPHORE_LIMIT = 5

    def __init__(
        self,
        region_service: RegionService,
        vacancies_repository: VacanciesRepository,
        favorites_repository: FavoritesRepository,
        hh_client_api: HHClient,
        tv_client_api: TVClient,
        vacancies_parser: VacanciesParsingService,
    ):
        self.region_service = region_service
        self.vacancies_repository = vacancies_repository
        self.favorites_repository = favorites_repository
        self.hh_client_api = hh_client_api
        self.tv_client_api = tv_client_api
        self.vacancies_parser = vacancies_parser
        self.semaphore = asyncio.Semaphore(self.SEMAPHORE_LIMIT)

    async def validation_and_get_region_data(self, location: str, region_code: str) -> dict:
        """
        Валидирует наименование населенного пункта и возвращает данные региона.

        Args:
            location: Наименование населенного пункта для валидации.
            region_code: Код региона для получения данных.

        Returns:
            Словарь, содержащий нормализованное наименование населенного пункта
            и данные региона.

        Raises:
            LocationValidationError: Если наименование населенного пункта некорректно.
            RegionNotFoundError: Если регион по `region_code` не найден.
        """
        logger.info(
            "Данные, полученные на валидацию: region_code - %s; location - %s",
            region_code, location
        )
        validated_data = {
            "location": self._location_name_verification(
                location=location
            ),
            "region_data": await self.region_service.get_region_by_code(
                region_code_tv=region_code
            )
        }
        logger.info("Данные после валидации: %s", pformat(validated_data))
        return validated_data

    async def get_vacancies_info(self, location: str, region_data: dict) -> dict:
        """
        Инициирует поиск, сбор, сохранение и возврат вакансий.

        Собирает вакансии из внешних API, сохраняет их в базу данных,
        предварительно удалив старые записи для данной локации, и возвращает
        собранные данные вместе со статистикой.

        Args:
            location: Нормализованное наименование населенного пункта.
            region_data: Словарь с данными о регионе.

        Returns:
            Словарь с результатами поиска, включая списки вакансий и информацию об ошибках.

        Raises:
            VacanciesServiceError: Если не удалось получить данные ни из одного источника.
        """
        logger.info(
            "Данные для поиска вакансий: region_data - %s; location - %s",
            pformat(region_data), location
        )

        region_name = region_data.get("name")
        api_vacancies_response = await self._get_vacancies_data_from_apis(
            location=location, region_data=region_data
        )
        
        error_request_hh = api_vacancies_response.get("error_request_hh")
        error_request_tv = api_vacancies_response.get("error_request_tv")
        all_vacancies_count = api_vacancies_response.get("all_vacancies_count")

        if error_request_hh and error_request_tv:
            logger.error("Не удалось получить или обработать данные вакансий со всех источников")
            raise VacanciesServiceError(
                error_details="Unable to retrieve or process vacancy data from all sources."
            )

        await self._save_vacancies_data(
            all_vacancies_count=all_vacancies_count,
            location=location,
            vacancies=api_vacancies_response.get("vacancies"),
        )

        logger.info(
            "Поиск и сохранение вакансий для '%s' в регионе '%s' завершен. "
            "Всего найдено: %d вакансий.",
            location, region_name, all_vacancies_count
        )

        api_vacancies_response.update({"location": location, "region_name": region_name})
    
        return api_vacancies_response

    async def get_vacancies_by_location(
        self, location: str, page: int, page_size: int
    ):
        """
        Возвращает пагинированный список вакансий для указанной локации.

        Args:
            location: Наименование населенного пункта.
            page: Номер страницы.
            page_size: Количество элементов на странице.

        Returns:
            Объект `VacanciesListSchema` с пагинированным списком вакансий.

        Raises:
            VacanciesServiceError: В случае ошибки валидации данных.
        """
        logger.info(
            "Получение списка вакансий по локации: %s, "
            "страница: %s, размер страницы: %s",
            location, page, page_size
        )

        total = await self.vacancies_repository.get_count_vacancies(
            location=location
        )
        if total == 0:
            items = []
        else:
            vacancies = await self.vacancies_repository.get_vacancies(
                location=location, page=page, page_size=page_size
            )

            try:
                items = [
                        VacancyOutSchema.model_validate(vacancy) for vacancy in vacancies
                    ]
            except ValidationError as error:
                raise VacanciesServiceError(
                    error_details="An error occurred during data validation for the vacancy list."
                ) from error

        logger.info(
            "Для локации: %s, страницы %s с размером страницы %s, найдено %s вакансий.",
            location, page, page_size, len(items)
        )

        return VacanciesListSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    async def get_vacancy_details(self, vacancy_id: str) -> dict:
        """
        Возвращает детальную информацию по одной вакансии.

        Получает данные из БД, затем актуализирует их, обращаясь к внешнему API
        соответствующего источника (`hh.ru` или `Работа России`).

        Args:
            vacancy_id: Уникальный идентификатор вакансии.

        Returns:
            Объект `VacancyDetailsOutSchema` с детальной информацией о вакансии.

        Raises:
            VacanciesServiceError: В случае ошибки валидации или при неизвестном источнике.
            VacancyNotFoundError: Если вакансия не найдена в БД или API.
        """
        logger.info(
            "Обработка запроса на получение подробной информации по вакансии с vacancy_id: %s", vacancy_id
        )

        vacancy = await self._get_vacancy_by_id(vacancy_id=vacancy_id)

        if vacancy.vacancy_source == 'hh.ru':
            vacancy_details_raw = await self._get_vacancy_details_hh_api(
                vacancy_id=vacancy.vacancy_id
            )
        elif vacancy.vacancy_source == 'Работа России':
            vacancy_details_raw = await self._get_vacancy_details_tv_api(
                vacancy_id=vacancy.vacancy_id,
                employer_code=vacancy.employer_code
            )
        else:
            logger.info(
                f'Неизвестный источник ({vacancy.vacancy_source}) для вакансии с vacancy_id={vacancy_id}.'
            )
            raise VacanciesServiceError(
                error_details=f"Unknown source ('{vacancy.vacancy_source}') for the vacancy."
            )
        
        logger.info(
            "Детальная информация по вакансии с vacancy_id=%s из источника - %s:\n%s",
            vacancy_id, vacancy.vacancy_source, pformat(vacancy_details_raw)
        )

        try:
            vacancy_details = VacancyDetailsOutSchema.model_validate(vacancy_details_raw)
            return vacancy_details
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="An error occurred during data validation for the vacancy details."
            ) from error

    async def add_vacancy_to_favorites(self, vacancy_id: str, user_id: int) -> None:
        """
        Добавляет вакансию в список избранного для пользователя.

        Args:
            vacancy_id: Идентификатор вакансии для добавления.
            user_id: Идентификатор пользователя.
        """
        logger.info(
            "Обработка запроса на добавление вакансии с vacancy_id: %s, "
            "от пользователя с user_id: %s",
            vacancy_id, user_id
        )

        vacancy = await self._get_vacancy_by_id(vacancy_id=vacancy_id)

        try:
            vacancy_dict = VacancyDetailsOutSchema.model_dump(vacancy)
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="An error occurred during data validation for the vacancy details."
            ) from error
    
        await self.favorites_repository.add_vacancy(
            favorite_data={"user_id": user_id, **vacancy_dict}
        )
    
    async def delete_vacancy_from_favorites(self, vacancy_id: str, user_id: int) -> None:
        """
        Удаляет вакансию из списка избранного пользователя.

        Args:
            vacancy_id: Идентификатор вакансии для удаления.
            user_id: Идентификатор пользователя.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена в избранном у пользователя.
        """
        logger.info(
            "Обработка запроса на удаление вакансии с vacancy_id: %s, "
            "от пользователя с user_id: %s",
            vacancy_id, user_id
        )
        delete_result = await self.favorites_repository.delete_vacancy(
            user_id=user_id, vacancy_id=vacancy_id,
        )
        if not delete_result:
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="The specified vacancy was not found in the user's favorites."
            )

    async def get_user_favorites(self, user_id: int, page: int, page_size: int) -> FavoriteVacanciesListSchema:
        """
        Возвращает пагинированный список избранных вакансий пользователя.

        Получает базовые данные из БД, затем обогащает их актуальной
        информацией из внешних API.

        Args:
            user_id: Идентификатор пользователя.
            page: Номер страницы.
            page_size: Количество элементов на странице.

        Returns:
            Объект `FavoriteVacanciesListSchema` с пагинированным списком
            детализированных вакансий.

        Raises:
            VacanciesServiceError: В случае ошибки валидации данных.
        """
        logger.info(
            "Получение избранных вакансий для пользователя id=%s, страница: %s, размер страницы: %s",
            user_id, page, page_size
        )

        total = await self.favorites_repository.get_count_favorites_vacancies(
            user_id=user_id
        )
        if total == 0:
            return FavoriteVacanciesListSchema(
                total=0, page=page, page_size=page_size, items=[]
            )

        logger.info("Для пользователя user_id=%s найдено %s вакансий в избранном", user_id, total)
        vacancies_raw = await self.favorites_repository.get_favorites_vacancies(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        logger.info(f"pformat(vacancies_raw) {pformat(vacancies_raw)}")
        compiled_vacancies = await self._compile_enriched_favorite_vacancies(
            vacancies_raw=vacancies_raw
        )

        try:
            items = [
                VacancyDetailsOutSchema.model_validate(vacancy) for vacancy in compiled_vacancies
            ]
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="An error occurred during data validation for the favorite vacancies list."
            ) from error

        return FavoriteVacanciesListSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    # Блок приватных методов для валидации населенного пункта и получения данных региона
    def _normalize_location(self, parts: list[str], hyphen: bool) -> str:
        """Нормализует наименование населённого пункта к единому формату."""
        return (
            "-".join(part.capitalize() for part in parts)
            if hyphen else
            " ".join(part.capitalize() for part in parts)
        )

    def _is_hyphen_exist(self, location: str) -> tuple[bool, str]:
        """Проверяет наличие дефиса в названии населенного пункта и разделяет его."""
        if "-" in location:
            split_location = location.split("-")
            hyphen = True
            return hyphen, split_location
    
        split_location = location.split()
        hyphen = False
        return hyphen, split_location
    
    def _validate_location(self, location: str, split_location: list[str]) -> None:
        """Проверяет корректность наименования населенного пункта."""
        if len(split_location) > self.MAX_COUNT_PARTS_IN_LOCATION:
            raise LocationValidationError(
                location=location,
                error_details=(
                    f"The location name consists of too many parts. "
                    f"Number of parts: {len(split_location)}, maximum: {self.MAX_COUNT_PARTS_IN_LOCATION}."
                )
            )
        
        if not all(
            symbol.isspace() or symbol.isalpha()
            for symbol in (part_name for part_name in split_location)
        ):
            raise LocationValidationError(
                location=location,
                error_details="The location name must not contain numbers."
            )
        
        if not re.search(r"^[А-Яа-яЁё\s\-]+\Z", location):
            raise LocationValidationError(
                location=location,
                error_details="The location name must contain only Russian letters."
            )
    
    def _location_name_verification(self, location: str) -> str:
        """Выполняет полную валидацию и нормализацию наименования населенного пункта."""
        hyphen, split_location = self._is_hyphen_exist(location=location)
        self._validate_location(location=location, split_location=split_location)
        return self._normalize_location(
            parts=split_location, hyphen=hyphen
        )

    # Блок приватных методов для получения вакансий в заданном регионе и локации
    async def _get_vacancies_data_from_apis(self, location: str, region_data: dict) -> dict:
        """Агрегирует данные о вакансиях из всех внешних API, выполняя запросы асинхронно."""
        region_code_hh = region_data.get("code_hh")
        region_code_tv = region_data.get("code_tv")

        logger.info(
            "Начинаю асинхронный сбор вакансий из внешних API для '%s' (коды региона: hh=%s, tv=%s)...",
            location, region_code_hh, region_code_tv
        )

        tasks = [
            self._get_vacancies_hh_api(location=location, region_code_hh=region_code_hh),
            self._get_vacancies_tv_api(location=location, region_code_tv=region_code_tv)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        vacancies = []
        vacancies_count_hh = 0
        vacancies_count_tv = 0
        error_request_hh = False
        error_request_tv = False
        error_details_hh = ""
        error_details_tv = ""

        # Process HH.ru results
        hh_result = results[0]
        if isinstance(hh_result, (VacanciesNotFoundError, HHAPIRequestError, VacancyParseError)):
            logger.error(
                "Ошибка при запросе или обработке данных от HH.ru API: %s",
                hh_result, exc_info=True
            )
            error_request_hh = True
            error_details_hh = getattr(hh_result, 'detail', str(hh_result))
        elif isinstance(hh_result, Exception):
            logger.error(
                "Непредвиденная ошибка при запросе или обработке данных от HH.ru API: %s",
                hh_result, exc_info=True
            )
            error_request_hh = True
            error_details_hh = str(hh_result)
        else:
            vacancies.extend(hh_result.get("vacancies", []))
            vacancies_count_hh = hh_result.get("vacancies_count", 0)

        # Process TrudVsem results
        tv_result = results[1]
        if isinstance(tv_result, (VacanciesNotFoundError, TVAPIRequestError, VacancyParseError)):
            logger.error(
                "Ошибка при запросе или обработке данных от trudvsem.ru API: %s",
                tv_result, exc_info=True
            )
            error_request_tv = True
            error_details_tv = getattr(tv_result, 'detail', str(tv_result))
        elif isinstance(tv_result, Exception):
            logger.error(
                "Непредвиденная ошибка при запросе или обработке данных от trudvsem.ru API: %s",
                tv_result, exc_info=True
            )
            error_request_tv = True
            error_details_tv = str(tv_result)
        else:
            vacancies.extend(tv_result.get('vacancies', []))
            vacancies_count_tv = tv_result.get('vacancies_count', 0)

        all_vacancies_count = vacancies_count_hh + vacancies_count_tv

        logger.info(
            "Асинхронный сбор вакансий из API завершен. Найдено: %d от hh.ru, %d от Работа России. Всего: %s",
            vacancies_count_hh, vacancies_count_tv, all_vacancies_count
        )

        return {
            "vacancies": vacancies,
            "error_request_hh": error_request_hh,
            "error_request_tv": error_request_tv,
            "error_details_hh": error_details_hh,
            "error_details_tv": error_details_tv,
            "all_vacancies_count": all_vacancies_count,
            "vacancies_count_hh": vacancies_count_hh,
            "vacancies_count_tv": vacancies_count_tv,
        }

    async def _get_vacancies_tv_api(self, location: str, region_code_tv: str) -> dict:
        """Получает и парсит вакансии с сайта 'Работа России'."""
        vacansies_raw = await self.tv_client_api.get_vacansies_in_region(
            region_code_tv=region_code_tv
        )
        if not vacansies_raw:
            raise VacanciesNotFoundError(
                source="trudvsem.ru API",
                region_code=region_code_tv,
                location=location
            )

        vacancies = self.vacancies_parser.parce_vacancies_tv(
            vacancies=vacansies_raw, location=location
        )

        return {"vacancies": vacancies, "vacancies_count": len(vacancies)}

    async def _get_vacancies_hh_api(self, location: str, region_code_hh: str) -> dict:
        """Получает и парсит вакансии с сайта 'hh.ru'."""
        vacansies_raw = await self.hh_client_api.get_vacansies_in_location(
            location=location,
            region_code_hh=region_code_hh
        )
        if not vacansies_raw:
            raise VacanciesNotFoundError(
                source="HH.ru API",
                region_code=region_code_hh,
                location=location
            )

        vacancies = self.vacancies_parser.parce_vacancies_hh(
            vacancies=vacansies_raw, location=location
        )
        return {"vacancies": vacancies, "vacancies_count": len(vacansies_raw)}

    async def _save_vacancies_data(
        self,
        all_vacancies_count: int,
        location: str,
        vacancies: list[dict]
    ) -> None:
        """Сохраняет данные о вакансиях в БД, предварительно удаляя старые."""
        logger.info("Начинаю обновление вакансий в БД для локации '%s'.", location)

        await self.vacancies_repository.delete_vacancies_by_location(
            location=location
        )

        if all_vacancies_count > 0:
            await self.vacancies_repository.save_vacancies(
                vacancies=vacancies
            )
            logger.info(
                "БД обновлена: сохранено %d новых вакансий для локации '%s'.",
                all_vacancies_count, location
            )
        else:
            logger.info(
                "БД обновлена: новые вакансии для локации '%s' не найдены, старые данные удалены.",
                location
            )

    # Блок приватных методов для запроса информации по отдельной вакансии
    async def _get_vacancy_details_hh_api(self, vacancy_id: str):
        """Получает и парсит детальную информацию о вакансии от hh.ru API."""
        vacancy_request_result = await self.hh_client_api.get_one_vacancy(
            vacancy_id=vacancy_id
        )

        search_status = vacancy_request_result.get("search_status")
        if search_status == self.FLAG_VACANCY_NOT_FOUND:
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Could not find vacancy details on the external source (hh.ru)."
            )

        vacancy_raw = vacancy_request_result.get("response_data")

        return self.vacancies_parser.parce_vacancy_details_hh(vacancy=vacancy_raw)

    async def _get_vacancy_details_tv_api(self, vacancy_id: str, employer_code: str):
        """Получает и парсит детальную информацию о вакансии от trudvsem.ru API."""
        vacancy_raw = await self.tv_client_api.get_one_vacancy(
            vacancy_id=vacancy_id,
            employer_code=employer_code
        )
        if not vacancy_raw:
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Could not find vacancy details on the external source (trudvsem.ru)."
            )
        
        return self.vacancies_parser.parce_vacancy_details_tv(
            vacancy=vacancy_raw
        )

    async def _get_vacancy_by_id(self, vacancy_id: str) -> Vacancies:
        """Возвращает данные вакансии из БД по ее ID."""
        vacancy_raw = await self.vacancies_repository.get_vacancy_by_id(
            vacancy_id=vacancy_id
        )
        if not vacancy_raw:
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="A vacancy with the specified ID was not found."
            )

        try:
            vacancy = VacancyOutSchema.model_validate(vacancy_raw)
            return vacancy
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="An error occurred during data validation."
            ) from error

    async def _fetch_one_favorite_vacancy(self, vacancy: FavoriteVacancies) -> dict:
        """
        Асинхронно получает детальную информацию по одной вакансии,
        контролируя количество одновременных запросов с помощью семафора.
        В случае ошибки возвращает исходные данные с измененным статусом.
        """
        async with self.semaphore:
            try:
                if vacancy.vacancy_source == "hh.ru":
                    return await self._get_vacancy_details_hh_api(
                        vacancy_id=vacancy.vacancy_id
                    )
                if vacancy.vacancy_source == "Работа России":
                    return await self._get_vacancy_details_tv_api(
                        vacancy_id=vacancy.vacancy_id,
                        employer_code=vacancy.employer_code,
                    )
                # Если источник неизвестен, логируем и возвращаем как "не найдено"
                logger.warning(
                    "Unknown vacancy source '%s' for favorite vacancy ID %s.",
                    vacancy.vacancy_source, vacancy.vacancy_id
                )
                raise VacancyNotFoundError(vacancy_id=vacancy.vacancy_id)

            except (VacancyNotFoundError, HHAPIRequestError, TVAPIRequestError) as error:
                logger.error(
                    "Failed to fetch details for favorite vacancy %s: %s",
                    vacancy.vacancy_id, error
                )
                # Используем Pydantic схему для преобразования в словарь
                vacancy_dict = VacancyDetailsOutSchema.model_dump(vacancy)
                vacancy_dict["status"] = self.FLAG_VACANCY_NOT_FOUND
                return vacancy_dict

    async def _compile_enriched_favorite_vacancies(
        self, vacancies_raw: list[FavoriteVacancies]
    ) -> list:
        """
        Обогащает список избранных вакансий актуальными данными из внешних API,
        используя семафор для ограничения одновременных запросов.
        """
        logger.info("Обогащение и актуализация вакансий, добавленных в избранное")

        tasks = [self._fetch_one_favorite_vacancy(vacancy) for vacancy in vacancies_raw]
        compiled_vacancies = await asyncio.gather(*tasks)

        return compiled_vacancies
