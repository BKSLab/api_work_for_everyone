import logging
from pprint import pformat

import httpx
from fastapi import status

from core.settings import get_settings
from exceptions.api_clients import HHAPIRequestError

settings = get_settings()
logger = logging.getLogger(__name__)


class HHClient:
    """Клас для взаимодействия API hh.ru для загрузки вакансий."""

    SOCIAL_PROTECTED_HH: str = 'accept_handicapped'
    VACANCIES_PER_ONE_PAGE_HH: int = 100
    FIRST_PAGE: int = 0
    FIRST_ELEMENT: int = 1
    VACANCY_URL: str = "https://api.hh.ru/vacancies/"

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client
        self.headers = {
            "Authorization": f"Bearer {settings.app.access_token_hh.get_secret_value()}"
        }
            
    async def _request_to_api_hh(self, url: str, params: dict | None = None) -> dict:
        """Запрос к API портала 'hh.ru'."""
        logger.info("Запрос к HH API. URL: %s, Параметры: %s", url, pformat(params))
        try:
            response = await self.httpx_client.get(
                url=url,
                headers=self.headers,
                params=params or {},
            )

            response.raise_for_status()
            response_data = response.json()
            return {"status": True, "search_status": "success", "response_data": response_data}

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code
            if status_code == status.HTTP_404_NOT_FOUND:
                logger.warning(
                    "Поиск по HH API не дал результатов (404 Not Found). URL: %s, Параметры: %s",
                    error.request.url, pformat(params),
                )
                return {"status": True, "search_status": "not_found", "response_data": {}}

            logger.error(
                "Ошибка статуса HTTP при запросе к HH API. Статус: %s, URL: %s, Ответ: %s",
                status_code, error.request.url, error.response.text,
            )
            return {"status": False, "search_status": "request_error", "response_data": {}}

        except httpx.RequestError as error:
            logger.error(
                "Ошибка запроса к HH API. URL: %s, Ошибка: %s",
                error.request.url, error,
            )
            return {"status": False, "search_status": "request_error", "response_data": {}}

        except Exception as error:
            logger.error(
                "Непредвиденная ошибка в _request_to_api_hh. Ошибка: %s",
                error,exc_info=True,
            )
            return {"status": False, "search_status": "request_error", "response_data": {}}

    async def _get_many_vacansies_in_location(
        self,
        region_code_hh: str,
        location: str,
        count_pages: int,
        first_page_vacansies: list,
    ):
        """Загружает вакансии, когда страниц больше чем одна."""
        logger.info(
            'Загрузка нескольких страниц вакансий. Регион: %s, Локация: %s, Страниц: %s',
            region_code_hh,
            location,
            count_pages,
        )
        all_vacancies = first_page_vacansies.copy()
        for page in range(1, count_pages):
            logger.info('Загрузка страницы %s из %s.', page + 1, count_pages)
            params = {
                "page": page,
                "per_page": self.VACANCIES_PER_ONE_PAGE_HH,
                "area": region_code_hh,
                "text": location,
                "label": self.SOCIAL_PROTECTED_HH,
            }
            vacansies_request_result = await self._request_to_api_hh(
                url=self.VACANCY_URL, params=params
            )
            status = vacansies_request_result.get("status")
            if not status:
                raise HHAPIRequestError(
                    error_details="Failed to load vacansies postings when multi-page loading.",
                    request_url=self.VACANCY_URL,
                    request_params=params
                )
            response_data: dict = vacansies_request_result.get("response_data", {})
            vacancies_for_page: list = response_data.get('items', [])
            all_vacancies.extend(vacancies_for_page)

        logger.info('Всего загружено %s вакансий.', len(all_vacancies))
        return all_vacancies

    async def get_vacansies_in_location(
        self, location: str, region_code_hh: str,
    ) -> list[dict]:
        """Получение данных вакансий в регионе."""
        logger.info("Поиск вакансий на hh.ru. Регион: %s, Локация: %s", region_code_hh, location)
        params = {
            "page": self.FIRST_PAGE,
            "per_page": self.VACANCIES_PER_ONE_PAGE_HH,
            "area": region_code_hh,
            "text": location,
            "label": self.SOCIAL_PROTECTED_HH,
        }
        vacansies_request_result = await self._request_to_api_hh(
            url=self.VACANCY_URL, params=params
        )
        status = vacansies_request_result.get("status")
        if not status:
            raise HHAPIRequestError(
                error_details="Failed to complete first request while loading vacancies.",
                request_url=self.VACANCY_URL,
                request_params=params
            )

        response_data: dict = vacansies_request_result.get("response_data", {})
        count_pages = response_data.get("pages", 0)
        logger.info("Найдено %s страниц с вакансиями.", count_pages)
        
        found_vacancies = response_data.get("items", [])
        if count_pages > self.FIRST_ELEMENT:
            found_vacancies = await self._get_many_vacansies_in_location(
                region_code_hh=region_code_hh,
                location=location,
                count_pages=count_pages,
                first_page_vacansies=found_vacancies,
            )
        
        logger.info(
            "Найдено %s вакансий для региона %s и локации %s.",
            len(found_vacancies), region_code_hh, location,
        )
        return found_vacancies

    async def get_one_vacancy(self, vacancy_id: str) -> dict:
        """Получение подробную информацию по одной вакаснии."""
        logger.info("Поиск одной вакансии по vacancy_id=%s", vacancy_id)
        request_url = "".join([self.VACANCY_URL, vacancy_id])
        vacancy_request_result = await self._request_to_api_hh(
            url=request_url
        )
        status = vacancy_request_result.get("status")
        search_status = vacancy_request_result.get("search_status")
        if not status:
            raise HHAPIRequestError(
                error_details="Failed to complete request while retrieving data for one vacancy.",
                request_url=request_url
            )
        
        if search_status == "success":
            logger.info("Вакансия с vacancy_id=%s успешно найдена.", vacancy_id)
        elif search_status == "not_found":
            logger.warning("Вакансия с vacancy_id=%s не найдена.", vacancy_id)
            
        return vacancy_request_result
    