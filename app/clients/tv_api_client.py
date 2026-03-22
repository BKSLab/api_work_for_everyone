import asyncio
import logging
from math import ceil
from pprint import pformat

import httpx

from exceptions.api_clients import TVAPIRequestError

logger = logging.getLogger(__name__)


class TVClient:
    """Клас для взаимодействия API trudvsem.ru для загрузки вакансий."""

    SOCIAL_PROTECTED: str = "Инвалид"
    VACANCIES_PER_ONE_PAGE: int = 100
    FIRST_ELEMENT_LIST: int = 0
    FIRST_ELEMENT: int = 1

    ENDPOINT_REGION: str = (
        "http://opendata.trudvsem.ru/api/v1/vacancies/region/"
    )
    ONE_VACANCY_ENDPOINT: str = (
        "http://opendata.trudvsem.ru/api/v1/vacancies/vacancy"
    )

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client

    async def _request_to_api_tv(self, url: str, params: dict | None = None) -> dict:
        """Запрос к API портала 'trudvsem.ru'."""
        logger.info(
            "🌐 Запрос к API trudvsem.ru. URL: %s, параметры: %s",
            url, pformat(params)
        )
        try:
            response = await self.httpx_client.get(
                url=url,
                params=params or {},
            )
            response.raise_for_status()
            response_data = response.json()
            return {"status": True, "response_data": response_data}

        except httpx.HTTPStatusError as error:
            status_code = error.response.status_code
            logger.error(
                "❌ Ошибка HTTP при запросе к API trudvsem.ru. Статус: %s, URL: %s, ответ: %s",
                status_code, error.request.url, error.response.text,
            )
        except httpx.RequestError as error:
            logger.error(
                "❌ Ошибка сети при запросе к API trudvsem.ru. URL: %s, детали: %s",
                error.request.url, error,
            )
        except Exception as error:
            logger.error(
                "❌ Непредвиденная ошибка при запросе к API trudvsem.ru. Детали: %s",
                error, exc_info=True,
            )
        return {"status": False, "response_data": {}}

    def _get_count_pages(self, total_vacancies: int) -> int:
        """Возвращает количество страниц при запросе вакансий."""
        return ceil(total_vacancies / self.VACANCIES_PER_ONE_PAGE)

    def _create_vacancies_tasks(self, request_url: str, count_pages: int) -> list:
        """Создает список задач (корутин) для запроса вакансий."""
        return [
            self._request_to_api_tv(
                url=request_url,
                params={
                    "social_protected": self.SOCIAL_PROTECTED,
                    "limit": self.VACANCIES_PER_ONE_PAGE,
                    "offset": page
                }
            )
            for page in range(1, count_pages)
        ]

    # TODO: посмотреть, что тут не так с исключенияями
    async def _get_many_vacancies_in_region(
        self,
        request_url: str,
        region_code_tv: str,
        count_pages: int,
        first_page_vacancies: list[dict]
    ) -> list[dict]:
        """Получение данных вакансий в регионе по нескольким страницам."""
        try:
            tasks = self._create_vacancies_tasks(request_url, count_pages)

            # Параллельное выполнение всех запросов
            vacancies_request_result: list[dict] = await asyncio.gather(*tasks, return_exceptions=True)
            for result in vacancies_request_result:
                try:
                    status = result.get("status")
                    response_data: dict = result.get("response_data")
                    if not status:
                        raise TVAPIRequestError(
                            error_details="Ошибка при загрузке вакансий (многостраничный запрос).",
                            request_url=request_url,
                            request_params={
                                "social_protected": self.SOCIAL_PROTECTED,
                                "region_code_tv": region_code_tv,
                            }
                        )
                    vacancies_for_page: list = response_data.get("results", {}).get("vacancies", [])
                    first_page_vacancies.extend(vacancies_for_page)
                except Exception as error:
                    logger.error(
                        "❌ Ошибка при обработке данных API trudvsem.ru. Детали: %s, результат: %s",
                        error, result, exc_info=True,
                    )
                    raise TVAPIRequestError(
                        error_details="Ошибка при загрузке вакансий (многостраничный запрос).",
                        request_url=request_url,
                        request_params={
                            "social_protected": self.SOCIAL_PROTECTED,
                            "region_code_tv": region_code_tv,
                        }
                    )
            return first_page_vacancies
        except TVAPIRequestError:
            raise

    async def get_vacancies_in_region(self, region_code_tv: str) -> list[dict]:
        """Получение данных вакансий в регионе."""
        logger.info("🔍 Поиск вакансий на trudvsem.ru. Код региона: %s", region_code_tv)

        request_params = {"social_protected": self.SOCIAL_PROTECTED}
        request_url = self.ENDPOINT_REGION + region_code_tv
        vacancies_request_result = await self._request_to_api_tv(
            url=request_url, params=request_params
        )

        status = vacancies_request_result.get("status")
        response_data: dict = vacancies_request_result.get("response_data")
        first_page_vacancies = response_data.get("results", {}).get("vacancies", [])

        if not status:
            raise TVAPIRequestError(
                error_details="Ошибка при выполнении первого запроса вакансий.",
                request_url=request_url,
                request_params=request_params
            )

        count_pages = self._get_count_pages(
            total_vacancies=response_data.get("meta", {}).get("total")
        )
        logger.info("📋 Найдено страниц с вакансиями (trudvsem.ru): %s.", count_pages)
        if count_pages > self.FIRST_ELEMENT:
            return await self._get_many_vacancies_in_region(
                request_url=request_url,
                region_code_tv=region_code_tv,
                count_pages=count_pages,
                first_page_vacancies=first_page_vacancies
            )
        return first_page_vacancies

    async def get_one_vacancy(self, vacancy_id: str, employer_code: str) -> dict:
        """Получение данных по одной вакансии."""
        logger.info("🔍 Запрос детальной информации по вакансии trudvsem.ru. ID: %s", vacancy_id)
        request_url = "/".join(
            [
                self.ONE_VACANCY_ENDPOINT,
                employer_code,
                vacancy_id,
            ]
        )
        vacancy_request_result = await self._request_to_api_tv(url=request_url)
        status = vacancy_request_result.get("status")
        if not status:
            raise TVAPIRequestError(
                error_details="Ошибка при запросе детальной информации по вакансии.",
                request_url=request_url
            )

        vacancy: dict = vacancy_request_result.get("response_data")
        return vacancy.get("results", {}).get("vacancies", [None])[0].get("vacancy", {})
