from pprint import pprint
import re

from clients.hh_api_client import HHClient
from clients.tv_api_client import TVClient
from core.config_logger import logger
from exceptions.repository_exceptions import RegionRepositoryError
from exceptions.service_exceptions import (
    InvalidLocationError,
    RegionNotFoundError,
    TVAPIRequestError,
    VacanciesNotFoundError,
    VacancyParseError
)
from repositories.vacancies_repository import VacanciesRepository
from services.region_service import RegionService


class VacanciesService:
    """
    Сервис для работы с вакансиями. Загрузка,
    подготовка данных и сохранение вакансий в БД.
    """

    FIRST_ELEMENT_LIST = 0

    def __init__(
        self,
        region_service: RegionService,
        vacancies_repository: VacanciesRepository,
        hh_client_api: HHClient,
        tv_client_api: TVClient,
    ):
        self.region_service = region_service
        self.vacancies_repository = vacancies_repository
        self.hh_client_api = hh_client_api
        self.tv_client_api = tv_client_api

    async def normalize_location(self, parts: list[str], hyphen: bool) -> str:
        """Нормализует наименование населённого пункта."""
        return (
            '-'.join(part.capitalize() for part in parts)
            if hyphen else
            ' '.join(part.capitalize() for part in parts)
        )

    async def location_validation(self, location: str) -> str:
        """Валидирует наименование населенного пункта."""
        if '-' in location:
            split_location = location.split('-')
            hyphen = True
        else:
            split_location = location.split()
            hyphen = False
        if (
            len(split_location) <= 3
            and all(
                symbol.isspace() or symbol.isalpha()
                for symbol in (part_name for part_name in split_location)
            )
            and re.search(r'^[А-Яа-яЁё\s\-]+\Z', location)
        ):
            return await self.normalize_location(
                parts=split_location, hyphen=hyphen
            )
        logger.warning(f'Invalid location: {location}')
        raise InvalidLocationError(location)

    async def validation_and_get_region_data(
        self, location: str, region_code: str
    ) -> dict:
        """
        Валидация наименование населенного пункта и получение данных региона
        для подготовки запроса на поиск вакансий.
        """
        logger.info(
            'Данные, полученные на валидацию:'
            f'\n - region_code: {region_code}\n = location: {location}'
        )
        try:
            return {
                'location': await self.location_validation(
                    location=location
                ),
                'region_data': await self.region_service.get_region_by_code(
                    region_code_tv=region_code
                )
            }
        except (
            RegionNotFoundError,
            RegionRepositoryError,
            InvalidLocationError
        ):
            raise
    
    async def parce_vacancies_tv(
        self, vacancies: list[dict], location: str
    ) -> dict:
        """
        Обрабатывает данные о вакансиях, полученных от API trudvsem.ru.
        Данные обрабатываются перед сохранением данных в БД
        """
        pattern = rf'(?i)\b{location}\b'
        vacancies_lst = []
        for vacancy in vacancies:
            if vacancy.get('duty'):
                duty = (
                    re.sub(r"<[^>]+>", "", vacancy.get('duty'), flags=re.S)
                    .replace('&nbsp;', '')
                    .replace('&nbsp', '')
                )
            else:
                duty = 'Работодатель не указал должностные обязанности'
            vacancy_location = (
                vacancy.get('vacancy')
                .get('addresses')
                .get('address')[self.FIRST_ELEMENT_LIST]
                .get('location')
            )
            if re.search(pattern, vacancy_location):
                contact_list = vacancy.get('vacancy').get('contact_list')
                if contact_list:
                    contact_phone_number = contact_list[
                        self.FIRST_ELEMENT_LIST
                    ].get('contact_value')
                else:
                    contact_phone_number = (
                        'Работодатель не указал контактный номер телефона'
                    )
                vacancies_lst.append(
                    {
                        'vacancy_name': vacancy.get('vacancy').get('job-name'),
                        'description': duty,
                        'salary': 'Работодатель не указал заработную плату.'
                        if vacancy.get('vacancy').get('salary') is None
                        else vacancy.get('vacancy').get('salary'),
                        'vacancy_source': 'Работа России',
                        'vacancy_url': vacancy.get('vacancy').get('vac_url'),
                        'employer_name': vacancy.get('vacancy')
                        .get('company')
                        .get('name'),
                        'employer_location': vacancy.get('vacancy')
                        .get('addresses')
                        .get('address')[
                            self.FIRST_ELEMENT_LIST
                        ]
                        .get('location'),
                        'employer_phone_number': contact_phone_number,
                        'company_code': vacancy.get('vacancy')
                        .get('company')
                        .get('companycode'),
                        'vacancy_id': vacancy.get('vacancy').get('id'),
                    }
                )
        return {'status': True, 'vacancies_lst': vacancies_lst}

    async def parce_vacancies_tv(self, vacancies: list[dict], location: str) -> dict:
        """
        Обрабатывает данные о вакансиях, полученных от API trudvsem.ru.
        Данные обрабатываются перед сохранением в БД и для построения рекомендаций.
        """
        pattern = rf'(?i)\b{location}\b'
        parsed_vacancies = []
        try:
            for vacancy_wrapper in vacancies:
                vacancy_data: dict = vacancy_wrapper.get('vacancy', {})

                # Местоположение
                addresses = vacancy_data.get('addresses', {}).get('address', [])
                vacancy_location = addresses[0].get('location') if addresses else ''
                if not re.search(pattern, vacancy_location):
                    continue

                # Должностные обязанности
                duty_raw = vacancy_data.get('duty')
                if duty_raw:
                    duty = (
                        re.sub(r"<[^>]+>", "", duty_raw, flags=re.S)
                        .replace('&nbsp;', '')
                        .replace('&nbsp', '')
                    )
                else:
                    duty = 'Работодатель не указал должностные обязанности'

                # Контактный номер
                contact_list = vacancy_data.get('contact_list') or []
                contact_phone_number = (
                    contact_list[0].get('contact_value')
                    if contact_list else 'Работодатель не указал контактный номер телефона'
                )

                # Требования
                requirement = vacancy_data.get('requirement', {})
                education = requirement.get('education', 'Не указано')
                experience = requirement.get('experience', 'Не указано')

                # Дополнительные поля
                category = vacancy_data.get('category', {}).get('specialisation', 'Не указано')
                work_place_type = vacancy_data.get('workPlaceType', {})
                workplace_quota = work_place_type.get('workPlaceQuota', False)
                disability_group = work_place_type.get('workPlaceDisabilityGroup', 'Не указано')

                parsed_vacancies.append({
                    'vacancy_id': vacancy_data.get('id'),
                    'vacancy_name': vacancy_data.get('job-name'),
                    'description': duty,
                    'salary': vacancy_data.get('salary') or 'Работодатель не указал заработную плату.',
                    'vacancy_url': vacancy_data.get('vac_url'),
                    'vacancy_source': 'Работа России',
                    'employer_name': vacancy_data.get('company', {}).get('name'),
                    'employer_location': vacancy_location,
                    'employer_phone_number': contact_phone_number,
                    'company_code': vacancy_data.get('company', {}).get('companycode'),
                    'education_required': education,
                    'experience_required': experience,
                    'category': category,
                    'workplace_quota': workplace_quota,
                    'disability_group': disability_group,
                    'employment_type': vacancy_data.get('employment'),
                    'schedule': vacancy_data.get('schedule'),
                    'conditions': vacancy_data.get('conditions', 'Не указаны'),
                })
            return parsed_vacancies
        except Exception as error:
            logger.exception(f'Ошибка при обработке вакансий от Trudvsem: {error}')
            raise VacancyParseError()

    async def get_vacancies_from_tv(self, location: str, region_data: dict) -> dict:
        """
        Получает количество вакансий по заданному региону и населенному
        пункту.
        """
        logger.info(
            'Данные, полученные на получение количества вакансий:'
            f'\n - location: {location}\n - region_data: {region_data}'
        )
        region_code_tv = region_data.get('region_code_tv')
        try:
            vacansies_raw = await self.tv_client_api.get_vacansies_in_region(
                region_code_tv=region_code_tv
            )
            if not vacansies_raw:
                logger.info(
                    'Вакансии от API "Работа России" не найдены '
                    f'для региона: {region_code_tv}'
                )
                raise VacanciesNotFoundError(region_code=region_code_tv)
            vacancies_count = len(vacansies_raw)
            logger.info(
                f'от API "Работа России" получено вакансий: {vacancies_count} '
                f'для региона: {region_code_tv}'
            )
            vacansies = await self.parce_vacancies_tv(
                vacancies=vacansies_raw, location=location
            )
            logger.info(f'Обработано вакансий по локации "{location}": {len(vacansies)}')
            return vacansies
        except (TVAPIRequestError, VacancyParseError):
            raise
