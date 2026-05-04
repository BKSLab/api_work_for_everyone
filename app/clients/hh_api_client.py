import asyncio
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

    # Ограничение параллельных запросов к HH.ru — сервер режет соединения по IP.
    # 3 одновременных запроса — рабочий предел для серверного IP.
    MAX_CONCURRENT_REQUESTS: int = 3

    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.5

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client
        self.headers = {
            "Authorization": f"Bearer {settings.app.access_token_hh.get_secret_value()}"
        }
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

    async def _request_to_api_hh(self, url: str, params: dict | None = None) -> dict:
        """Запрос к API портала 'hh.ru'."""
        logger.info("🌐 Запрос к API hh.ru. URL: %s, параметры: %s", url, pformat(params))
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
                    "⚠️ Запрос к API hh.ru не дал результатов (404). URL: %s, параметры: %s",
                    error.request.url, pformat(params),
                )
                return {"status": True, "search_status": "not_found", "response_data": {}}

            logger.error(
                "❌ Ошибка HTTP при запросе к API hh.ru. Статус: %s, URL: %s, ответ: %s",
                status_code, error.request.url, error.response.text,
            )
            return {"status": False, "search_status": "request_error", "response_data": {}}

        except httpx.RequestError as error:
            logger.error(
                "❌ Ошибка сети при запросе к API hh.ru. URL: %s, тип: %s, детали: %s",
                error.request.url, type(error).__name__, repr(error),
                exc_info=True,
            )
            return {"status": False, "search_status": "request_error", "response_data": {}}

        except Exception as error:
            logger.error(
                "❌ Непредвиденная ошибка при запросе к API hh.ru. Детали: %s",
                error, exc_info=True,
            )
            return {"status": False, "search_status": "request_error", "response_data": {}}

    # --- SEQUENTIAL BACKUP — раскомментировать для отката, если concurrent-версия сломается ---
    # async def _get_many_vacancies_in_location_sequential(
    #     self,
    #     region_code_hh: str,
    #     location: str,
    #     count_pages: int,
    #     first_page_vacancies: list,
    # ):
    #     """Загружает вакансии последовательно страница за страницей (резервная реализация)."""
    #     logger.info(
    #         '⚡ [SEQUENTIAL] Загрузка нескольких страниц вакансий (hh.ru). '
    #         'Регион: %s, населённый пункт: %s, страниц: %s',
    #         region_code_hh, location, count_pages,
    #     )
    #     all_vacancies = first_page_vacancies.copy()
    #     for page in range(1, count_pages):
    #         logger.info('📋 Загрузка страницы %s из %s (hh.ru).', page + 1, count_pages)
    #         params = {
    #             "page": page,
    #             "per_page": self.VACANCIES_PER_ONE_PAGE_HH,
    #             "area": region_code_hh,
    #             "text": location,
    #             "label": self.SOCIAL_PROTECTED_HH,
    #         }
    #         vacancies_request_result = await self._request_to_api_hh(
    #             url=self.VACANCY_URL, params=params
    #         )
    #         status = vacancies_request_result.get("status")
    #         if not status:
    #             raise HHAPIRequestError(
    #                 error_details="Ошибка при загрузке вакансий (многостраничный запрос).",
    #                 request_url=self.VACANCY_URL,
    #                 request_params=params
    #             )
    #         response_data: dict = vacancies_request_result.get("response_data", {})
    #         vacancies_for_page: list = response_data.get('items', [])
    #         all_vacancies.extend(vacancies_for_page)
    #     logger.info('✅ [SEQUENTIAL] Загрузка завершена (hh.ru). Всего вакансий: %s.', len(all_vacancies))
    #     return all_vacancies
    # --- END SEQUENTIAL BACKUP ---

    def _build_page_params(self, region_code_hh: str, location: str, page: int) -> dict:
        """Формирует параметры запроса для одной страницы вакансий."""
        return {
            "page": page,
            "per_page": self.VACANCIES_PER_ONE_PAGE_HH,
            "area": region_code_hh,
            "text": location,
            "label": self.SOCIAL_PROTECTED_HH,
        }

    async def _request_with_retry(self, url: str, params: dict | None = None) -> dict:
        """Выполняет запрос к API hh.ru с повторами при ошибке."""
        for attempt in range(1, self.MAX_RETRIES + 1):
            result = await self._request_to_api_hh(url=url, params=params)
            if result.get("status"):
                return result
            if attempt < self.MAX_RETRIES:
                logger.warning(
                    "⚠️ Попытка %d/%d не удалась (hh.ru). Повтор через %.1fс. URL: %s",
                    attempt, self.MAX_RETRIES, self.RETRY_DELAY, url,
                )
                await asyncio.sleep(self.RETRY_DELAY)
        return result

    async def _request_page_with_semaphore(self, region_code_hh: str, location: str, page: int) -> dict:
        """Запрашивает одну страницу вакансий с учётом семафора rate limit."""
        async with self._semaphore:
            params = self._build_page_params(region_code_hh, location, page)
            return await self._request_with_retry(url=self.VACANCY_URL, params=params)

    async def _get_many_vacancies_in_location(
        self,
        region_code_hh: str,
        location: str,
        count_pages: int,
        first_page_vacancies: list,
    ) -> list:
        """Загружает вакансии параллельно по всем страницам (concurrent-реализация).

        Страницы 1..count_pages-1 запрашиваются одновременно через asyncio.gather
        с ограничением MAX_CONCURRENT_REQUESTS для соблюдения rate limit HH.ru API.
        Страница 0 уже загружена вызывающим кодом и передаётся в first_page_vacancies.
        """
        logger.info(
            '⚡ [CONCURRENT] Загрузка нескольких страниц вакансий (hh.ru). '
            'Регион: %s, населённый пункт: %s, страниц: %s',
            region_code_hh, location, count_pages,
        )

        tasks = [
            self._request_page_with_semaphore(region_code_hh, location, page)
            for page in range(1, count_pages)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_vacancies = first_page_vacancies.copy()
        for page_num, result in enumerate(results, start=1):
            if isinstance(result, Exception):
                raise HHAPIRequestError(
                    error_details=f"Ошибка при параллельной загрузке страницы {page_num} (hh.ru): {result}",
                    request_url=self.VACANCY_URL,
                    request_params=self._build_page_params(region_code_hh, location, page_num),
                )
            if not result.get("status"):
                raise HHAPIRequestError(
                    error_details=f"Ошибка ответа API при загрузке страницы {page_num} (hh.ru).",
                    request_url=self.VACANCY_URL,
                    request_params=self._build_page_params(region_code_hh, location, page_num),
                )
            vacancies_for_page: list = result.get("response_data", {}).get("items", [])
            all_vacancies.extend(vacancies_for_page)

        logger.info('✅ [CONCURRENT] Загрузка завершена (hh.ru). Всего вакансий: %s.', len(all_vacancies))
        return all_vacancies

    async def get_vacancies_in_location(
        self, location: str, region_code_hh: str,
    ) -> list[dict]:
        """Получение данных вакансий в регионе."""
        logger.info("🔍 Поиск вакансий на hh.ru. Регион: %s, населённый пункт: %s", region_code_hh, location)
        params = {
            "page": self.FIRST_PAGE,
            "per_page": self.VACANCIES_PER_ONE_PAGE_HH,
            "area": region_code_hh,
            "text": location,
            "label": self.SOCIAL_PROTECTED_HH,
        }
        vacancies_request_result = await self._request_to_api_hh(
            url=self.VACANCY_URL, params=params
        )
        status = vacancies_request_result.get("status")
        if not status:
            raise HHAPIRequestError(
                error_details="Ошибка при выполнении первого запроса вакансий.",
                request_url=self.VACANCY_URL,
                request_params=params
            )

        response_data: dict = vacancies_request_result.get("response_data", {})
        count_pages = response_data.get("pages", 0)
        logger.info("📋 Найдено страниц с вакансиями (hh.ru): %s.", count_pages)

        found_vacancies = response_data.get("items", [])
        if count_pages > self.FIRST_ELEMENT:
            found_vacancies = await self._get_many_vacancies_in_location(
                region_code_hh=region_code_hh,
                location=location,
                count_pages=count_pages,
                first_page_vacancies=found_vacancies,
            )

        logger.info(
            "✅ Поиск вакансий на hh.ru завершён. Найдено: %s. Регион: %s, населённый пункт: %s.",
            len(found_vacancies), region_code_hh, location,
        )
        return found_vacancies

    async def get_one_vacancy(self, vacancy_id: str) -> dict:
        """Получение подробную информацию по одной вакаснии."""
        logger.info("🔍 Запрос детальной информации по вакансии hh.ru. ID: %s", vacancy_id)
        request_url = "".join([self.VACANCY_URL, vacancy_id])
        vacancy_request_result = await self._request_to_api_hh(
            url=request_url
        )
        status = vacancy_request_result.get("status")
        search_status = vacancy_request_result.get("search_status")
        if not status:
            raise HHAPIRequestError(
                error_details="Ошибка при запросе детальной информации по вакансии.",
                request_url=request_url
            )

        if search_status == "success":
            logger.info("✅ Вакансия hh.ru найдена. ID: %s", vacancy_id)
        elif search_status == "not_found":
            logger.warning("⚠️ Вакансия hh.ru не найдена. ID: %s", vacancy_id)

        return vacancy_request_result
