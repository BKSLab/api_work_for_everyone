import asyncio
from pprint import pprint
import httpx

from exceptions.service_exceptions import HHAPIRequestError
from core.config_logger import logger
from core.settings import get_settings


settings = get_settings()


class HHClient:
    """Клас для взаимодействия API hh.ru для загрузки вакансий."""

    SOCIAL_PROTECTED_HH: str = 'accept_handicapped'
    VACANCIES_PER_ONE_PAGE_HH: int = 100
    FIRST_PAGE: int = 0
    VACANCY_URL: str = 'https://api.hh.ru/vacancies/'

    def __init__(self, httpx_client: httpx.AsyncClient):
        self.httpx_client = httpx_client
        self.access_token_hh = settings.app.access_token_hh.get_secret_value()

    async def request_to_api_hh(self, url: str, params: dict) -> dict:
        """Запрос к API портала 'Работа России'."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token_hh}'}
            response = await self.httpx_client.get(
                url=url,
                headers=headers,
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
        raise HHAPIRequestError(params)

    async def get_many_vacansies_in_location(
        self,
        region_code_hh: str,
        location: str,
        count_pages: int,
        first_page_vacansies: list,
    ):
        try:
            tasks = [
                self.request_to_api_hh(
                    url=self.VACANCY_URL,
                    params={
                        'page': page,
                        'per_page': self.VACANCIES_PER_ONE_PAGE_HH,
                        'area': region_code_hh,
                        'text': location,
                        'label': self.SOCIAL_PROTECTED_HH,
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
                        vacancies_for_page: list = result.get('items', [])
                        first_page_vacansies.extend(vacancies_for_page)
                    except Exception as error:
                        logger.error(
                            'Ошибка при обработке данных из API TV: '
                            f'{type(error).__name__}: {str(error)}. '
                            f'Результат: {result}'
                        )
                        raise HHAPIRequestError(
                            params={
                                'region_code_hh': region_code_hh,
                                'location': location,
                                'count_pages': count_pages,
                            }
                        )
            return first_page_vacansies
        except HHAPIRequestError:
            raise

    async def get_vacansies_in_location(
        self,
        location: str,
        region_code_hh: str,
    ) -> list[dict]:
        """Получение данных вакансий в регионе."""
        try:
            params = {
                'page': self.FIRST_PAGE,
                'per_page': self.VACANCIES_PER_ONE_PAGE_HH,
                'area': region_code_hh,
                'text': location,
                'label': self.SOCIAL_PROTECTED_HH,
            }
            first_page_data = await self.request_to_api_hh(
                url=self.VACANCY_URL,
                params=params
            )
            count_pages = first_page_data.get('pages')
            if count_pages > 1:
                return await self.get_many_vacansies_in_location(
                    region_code_hh=region_code_hh,
                    location=location,
                    count_pages=count_pages,
                    first_page_vacansies=first_page_data.get('items', [])
                )
            return first_page_data.get('items', [])
        except HHAPIRequestError:
            raise
