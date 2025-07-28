import asyncio
from math import ceil

import httpx

from exceptions.service_exceptions import TVAPIRequestError
from core.config_logger import logger


class TVClient:
    """Клас для взаимодействия API trudvsem.ru для загрузки вакансий."""

    SOCIAL_PROTECTED: str = 'Инвалид'
    VACANCIES_PER_ONE_PAGE: int = 100
    FIRST_ELEMENT_LIST: int = 0
    ENDPOINT_REGION: str = (
        'http://opendata.trudvsem.ru/api/v1/vacancies/region/'
    )
    ONE_VACANCY_ENDPOINT: str = (
        'http://opendata.trudvsem.ru/api/v1/vacancies/vacancy'
    )

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client

    async def request_to_api_tv(self, url: str, params: dict) -> dict:
        """Запрос к API портала 'Работа России'."""
        try:
            response = await self.httpx_client.get(
                url=url,
                params=params,
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data
        except httpx.HTTPStatusError as error:
            logger.error(
                f'Получен HTTP статус {error.response.status_code} при '
                f'запросе к {url} api Битрикс. Текст ошибки: {error.response.text}.'
            )
        except httpx.RequestError as error:
            logger.error(
                f'Ошибка при запросе к {url}. api Битрикс'
                f'Тип ошибки: {type(error).__name__}. '
                f'Сообщение: {str(error)}.'
            )
        except Exception as error:
            logger.error(
                'При работе метода send_request_api_bitrix произошла '
                f'ошибка. Текст ошибки: {str(error)} '
                f'Тип ошибки: {type(error).__name__}.'
            )
        raise TVAPIRequestError(params)

    async def get_count_pages(self, total_vacansies: int) -> int:
        """Возвращает количество страниц при запросе вакансий."""
        return ceil(total_vacansies / self.VACANCIES_PER_ONE_PAGE)

    async def get_many_vacansies_in_region(
        self,
        region_code_tv: str,
        count_pages: int,
        first_page_vacansies: list[dict]
    ) -> list[dict]:
        """Получение данных вакансий в регионе по нескольким страницам."""
        try:
            tasks = [
                self.request_to_api_tv(
                    url=self.ENDPOINT_REGION + region_code_tv,
                    params={
                        'social_protected': self.SOCIAL_PROTECTED,
                        'limit': self.VACANCIES_PER_ONE_PAGE,
                        'offset': page
                    }
                )
                for page in range(1, count_pages)
            ]

            # Параллельное выполнение всех запросов
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(
                        f'Ошибка при выполнении запроса к API TV: '
                        f'{type(result).__name__}: {str(result)}'
                    )
                else:
                    try:
                        vacancies_for_page: list = result.get('results', {}).get('vacancies', [])
                        first_page_vacansies.extend(vacancies_for_page)
                    except Exception as error:
                        logger.error(
                            'Ошибка при обработке данных из API TV: '
                            f'{type(error).__name__}: {str(error)}. '
                            f'Результат: {result}'
                        )
                        raise TVAPIRequestError(
                            params={
                                'social_protected': self.SOCIAL_PROTECTED,
                                'region_code_tv': region_code_tv,
                            }
                        )
            return first_page_vacansies
        except TVAPIRequestError:
            raise

    async def get_vacansies_in_region(self, region_code_tv: str) -> list[dict]:
        """Получение данных вакансий в регионе."""
        try:
            first_page_data = await self.request_to_api_tv(
                url=self.ENDPOINT_REGION + region_code_tv,
                params={'social_protected': self.SOCIAL_PROTECTED}
            )
            count_pages = await self.get_count_pages(
                total_vacansies=first_page_data.get('meta', {}).get('total')
            )
            if count_pages > 1:
                return await self.get_many_vacansies_in_region(
                    region_code_tv=region_code_tv,
                    count_pages=count_pages,
                    first_page_vacansies=first_page_data.get('results', {}).get('vacancies', [])
                )
            return first_page_data.get('results', {}).get('vacancies', [])
        except TVAPIRequestError:
            raise
