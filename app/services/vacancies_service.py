import re
from pprint import pformat

from pydantic import ValidationError

from clients.hh_api_client import HHClient
from clients.tv_api_client import TVClient
from core.config_logger import logger
from exceptions.repository_exceptions import (
    RegionRepositoryError,
    VacanciesRepositoryError,
)
from exceptions.service_exceptions import (
    HHAPIRequestError,
    InvalidLocationError,
    RegionNotFoundError,
    TVAPIRequestError,
    VacanciesHHNotFoundError,
    VacanciesNotFoundError,
    VacanciesTVNotFoundError,
    VacancyHHNotFoundError,
    VacancyNotFoundError,
    VacancyParseError,
    VacancyTVNotFoundError,
)
from repositories.vacancies_repository import VacanciesRepository
from schemas.vacancies import (
    VacanciesListSchema,
    VacancyDetailsOutSchema,
    VacancyOutSchema,
)
from services.region_service import RegionService


class VacanciesService:
    """
    Сервис для работы с вакансиями. Загрузка,
    подготовка данных и сохранение вакансий в БД.
    """

    FIRST_ELEMENT_LIST = 0
    DEFAULT_LOCATION = 'Адрес не указан'
    DEFAULT_DUTY = 'Работодатель не указал должностные обязанности.'
    DEFAULT_PHONE = 'Работодатель не указал номер телефона'
    DEFAULT_EMAIL = 'Работодатель не указал адрес электронной почты.'
    DEFAULT_SALARY = 'Работодатель не указал заработную плату.'
    DEFAULT_NOT_SPECIFIED = 'Не указано'
    VACANCY_SOURCES = {
        'trudvsem': 'Работа России',
        'hh': 'HeadHunter',
    }

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

    async def parce_vacancy_details_tv(self, vacancy: dict) -> dict:
        """
        Обрабатывает данные о вакансии от API trudvsem.ru.
        """
        try:
            # Должностные обязанности
            duty_raw = vacancy.get('duty')
            if duty_raw:
                duty = (
                    re.sub(r"<[^>]+>", "", duty_raw, flags=re.S)
                    .replace('&nbsp;', '')
                    .replace('&nbsp', '')
                )
            else:
                duty = self.DEFAULT_DUTY
            
            # Местоположение
            addresses = (
                vacancy.get('addresses', {}).get('address', [])
            )

            vacancy_location = (
                (addresses[0] or {}).get('location')
                if addresses else self.DEFAULT_NOT_SPECIFIED
            ) or self.DEFAULT_NOT_SPECIFIED

            # заработная плата
            salary = vacancy.get('salary') or self.DEFAULT_SALARY

            # наименование работодателя
            employer_name = vacancy.get('company', {}).get('name')

            # код компании
            company_code = vacancy.get('company', {}).get('companycode')

            # Контактные данные
            contact_list = vacancy.get('contact_list') or []

            # Телефон
            contact_phone_number = next(
                (c['contact_value'] for c in contact_list if c.get('contact_type') == 'Телефон'),
                self.DEFAULT_PHONE
            )

            # Эл. почта
            contact_email = next(
                (c['contact_value'] for c in contact_list if c.get('contact_type') == 'Эл. почта'),
                self.DEFAULT_EMAIL
            )

            vacancy = {
                'vacancy_name': vacancy.get('job-name'),
                'vacancy_id': vacancy.get('id'),
                'vacancy_url': vacancy.get('vac_url'),
                'social_protected': vacancy.get('social_protected'),
                'vacancy_source': 'Работа России',
                'description': duty,
                'employer_location': vacancy_location,
                'salary': salary,
                'employer_name': employer_name,
                'company_code': company_code,
                'employer_phone': contact_phone_number,
                'employer_email': contact_email,
                'contact_person': vacancy.get('contact_person', self.DEFAULT_NOT_SPECIFIED),
                'employment': vacancy.get('employment', self.DEFAULT_NOT_SPECIFIED),
            }
            return vacancy
        except Exception as error:
            logger.exception(f'Ошибка при обработке вакансий от Trudvsem: {error}')
            raise VacancyParseError()

    async def parce_vacancy_details_hh(self, vacancy: dict) -> dict:
        """
        Обрабатывает данные о вакансии от API hh.ru.
        Приводит структуру к единому виду для внутреннего использования.
        """

        try:
            # --- Зарплата ---
            salary_info = vacancy.get('salary') or {}
            salary_from = salary_info.get('from')
            salary_to = salary_info.get('to')

            if not salary_info:
                salary = self.DEFAULT_SALARY
            elif salary_from and salary_to:
                salary = f'от {salary_from} до {salary_to}'
            elif salary_from:
                salary = f'от {salary_from}'
            elif salary_to:
                salary = f'до {salary_to}'
            else:
                salary = self.DEFAULT_SALARY

            # --- Описание ---
            description_raw = vacancy.get('description') or ''
            description = re.sub(r'<[^>]+>', '', description_raw, flags=re.S) or self.DEFAULT_NOT_SPECIFIED

            # --- Работодатель ---
            company_code = vacancy.get('employer_code', self.DEFAULT_NOT_SPECIFIED)
            employer = vacancy.get('employer') or {}
            employer_name = employer.get('name', self.DEFAULT_NOT_SPECIFIED)
            company_code = employer.get('id', self.DEFAULT_NOT_SPECIFIED)

            # --- Адрес ---
            address = vacancy.get('address') or {}
            employer_location = (
                (address or {}).get('raw') or self.DEFAULT_NOT_SPECIFIED
            )
            print(f'employer_location hh: {employer_location}')
            # --- Контакты ---
            contacts = vacancy.get('contacts') or {}
            employer_email = contacts.get('email') or self.DEFAULT_EMAIL
            phones = contacts.get('phones') or []
            employer_phone = phones[0].get('number') if phones and isinstance(phones[0], dict) else self.DEFAULT_PHONE

            employment = (
                vacancy.get('employment', {}).get('name')
                if isinstance(vacancy.get('employment'), dict)
                else self.DEFAULT_NOT_SPECIFIED
            )
            vacancy = {
                'vacancy_name': vacancy.get('name', self.DEFAULT_NOT_SPECIFIED),
                'vacancy_id': vacancy.get('id'),
                'vacancy_url': vacancy.get('alternate_url'),
                'social_protected': 'Инвалиды',
                'vacancy_source': 'hh.ru',
                'description': description,
                'employer_location': employer_location,
                'salary': salary,
                'employer_name': employer_name,
                'company_code': company_code,
                'employer_phone': employer_phone,
                'employer_email': employer_email,
                'contact_person': self.DEFAULT_NOT_SPECIFIED,
                'employment': employment,
            }
            return vacancy
        except Exception as error:
            logger.exception(f'Ошибка при обработке вакансий от hh.ru: {error}')
            raise VacancyParseError

    async def parce_vacancies_tv(
        self, vacancies: list[dict], location: str
    ) -> list[dict]:
        """
        Обрабатывает данные о вакансиях, полученных от API trudvsem.ru.
        Данные обрабатываются перед сохранением в БД.
        """
        pattern = rf'(?i)\b{location}\b'
        parsed_vacancies = []
        try:
            for vacancy_wrapper in vacancies:
                vacancy_data: dict = vacancy_wrapper.get('vacancy', {})

                # Местоположение
                addresses = (
                    vacancy_data.get('addresses', {}).get('address', [])
                )
                vacancy_location = (
                    addresses[0].get('location') if addresses
                    else ''
                ) or self.DEFAULT_NOT_SPECIFIED
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
                    duty = self.DEFAULT_DUTY

                # Контактный номер
                contact_list = vacancy_data.get('contact_list') or []
                contact_phone_number = (
                    contact_list[self.FIRST_ELEMENT_LIST].get('contact_value')
                    if contact_list else self.DEFAULT_PHONE
                )

                experience = (
                    vacancy_data.get('requirement', {})
                    .get('education', self.DEFAULT_NOT_SPECIFIED)
                )

                # Дополнительные поля
                category = (
                    vacancy_data.get('category', {}).get(
                        'specialisation', self.DEFAULT_NOT_SPECIFIED
                    )
                )
                salary = (
                    vacancy_data.get('salary') or self.DEFAULT_SALARY
                )
                company_code = (
                    vacancy_data.get('company', {}).get('companycode')
                )
                employer_name = vacancy_data.get('company', {}).get('name')
                parsed_vacancies.append(
                    {
                        'vacancy_id': vacancy_data.get('id'),
                        'location': location,
                        'name': vacancy_data.get('job-name'),
                        'description': duty,
                        'salary': salary,
                        'vacancy_url': vacancy_data.get('vac_url'),
                        'vacancy_source': self.VACANCY_SOURCES.get('trudvsem'),
                        'employer_name': employer_name,
                        'employer_location': vacancy_location,
                        'employer_phone': contact_phone_number,
                        'employer_code': company_code,
                        'experience_required': experience,
                        'category': category,
                        'employment_type': vacancy_data.get('employment') or self.DEFAULT_NOT_SPECIFIED,
                        'schedule': vacancy_data.get('schedule'),
                    }
                )
            return parsed_vacancies
        except Exception as error:
            logger.exception(f'Ошибка при обработке вакансий от Trudvsem: {error}')
            raise VacancyParseError()

    async def parce_vacancies_hh(
        self, vacancies: list[dict], location: str
    ) -> list[dict]:
        """
        Обрабатывает данные о вакансиях, полученных от API hh.ru.
        Данные обрабатываются перед сохранением в БД.
        """
        try:
            parsed_vacancies = []
            for vacancy in vacancies:
                # Зарплата
                salary_data = vacancy.get('salary')
                if not salary_data:
                    salary = self.DEFAULT_SALARY
                elif salary_data.get('from') and salary_data.get('to'):
                    salary = f"от {salary_data['from']} до {salary_data['to']}"
                elif salary_data.get('from'):
                    salary = f"от {salary_data['from']}"
                elif salary_data.get('to'):
                    salary = f"до {salary_data['to']}"
                else:
                    salary = self.DEFAULT_SALARY

                # Телефон
                contacts = vacancy.get('contacts') or {}
                phones = contacts.get('phones') or []
                if phones and phones[self.FIRST_ELEMENT_LIST].get('formatted'):
                    employer_phone_number = phones[self.FIRST_ELEMENT_LIST]['formatted']
                else:
                    employer_phone_number = self.DEFAULT_PHONE

                # Адрес
                address = vacancy.get('address')
                employer_location = (
                    address.get('raw') if address
                    else vacancy.get('area', {}).get('name', location)
                ) or self.DEFAULT_NOT_SPECIFIED

                # Название работодателя
                employer_name = (
                    (
                        vacancy.get('employer', {}).get('name', '')
                        .replace('Job development', '')
                        .replace('(', '').replace(')', '')
                    ) or self.DEFAULT_NOT_SPECIFIED
                )

                # Описание вакансии
                description = ''
                snippet = vacancy.get('snippet', {})
                if snippet.get('responsibility'):
                    description += snippet['responsibility']
                if snippet.get('requirement'):
                    description += '\n\nТребования: ' + snippet['requirement']
                company_code = (
                    vacancy.get('employer', {})
                    .get('id', self.DEFAULT_NOT_SPECIFIED)
                )
                experience_required = (
                    vacancy.get('experience', {})
                    .get('name', self.DEFAULT_NOT_SPECIFIED)
                )
                category = (
                    vacancy.get('professional_roles', [{}])[self.FIRST_ELEMENT_LIST]
                    .get('name', self.DEFAULT_NOT_SPECIFIED)
                )
                employment_type = (
                    vacancy.get('employment', {})
                    .get('name', self.DEFAULT_NOT_SPECIFIED)
                )
                schedule = (
                    vacancy.get('schedule', {})
                    .get('name', self.DEFAULT_NOT_SPECIFIED)
                )
                parsed_vacancies.append(
                    {
                        'vacancy_id': vacancy.get('id'),
                        'location': location,
                        'name': vacancy.get('name'),
                        'description': description.strip(),
                        'salary': salary,
                        'vacancy_url': vacancy.get('alternate_url'),
                        'vacancy_source': 'hh.ru',
                        'employer_name': employer_name,
                        'employer_location': employer_location,
                        'employer_phone': employer_phone_number,
                        'employer_code': company_code,
                        'experience_required': experience_required,
                        'category': category,
                        'employment_type': employment_type,
                        'schedule': schedule,
                    }
                )
            return parsed_vacancies
        except Exception as error:
            logger.exception(f'Ошибка при обработке вакансий от hh.ru: {error}')
            raise VacancyParseError()

    async def get_vacancies_tv_api(self, location: str, region_code_tv: str) -> dict:
        """
        Получает количество вакансий по заданному региону и населенному
        пункту на сайте 'Работа России'.
        """
        try:
            vacansies_raw = await self.tv_client_api.get_vacansies_in_region(
                region_code_tv=region_code_tv
            )
            if not vacansies_raw:
                logger.info(
                    'Вакансии от API "Работа России" не найдены '
                    f'для региона: {region_code_tv}'
                )
                raise VacanciesTVNotFoundError(
                    region_code=region_code_tv, location=location
                )
            vacansies = await self.parce_vacancies_tv(
                vacancies=vacansies_raw, location=location
            )
            vacancies_count = len(vacansies)
            logger.info(
                f'от API "Работа России" получено вакансий: {vacancies_count} '
                f'для региона: {region_code_tv}'
            )
            return {
                'vacansies': vacansies,
                'vacancies_count': vacancies_count,
            }
        except (TVAPIRequestError, VacancyParseError):
            raise

    async def get_vacancies_hh_api(self, location: str, region_code_hh: str) -> dict:
        """
        Получает количество вакансий по заданному региону и населенному
        пункту на сайте 'hh.ru'.
        """
        try:
            vacansies_raw = await self.hh_client_api.get_vacansies_in_location(
                location=location,
                region_code_hh=region_code_hh
            )
            if not vacansies_raw:
                logger.info(
                    'Вакансии от API "hh.ru" не найдены '
                    f'для региона: {region_code_hh} и населенного пункта: {location}'
                )
                raise VacanciesHHNotFoundError(
                    region_code=region_code_hh, location=location
                )
            vacancies_count = len(vacansies_raw)
            logger.info(
                f'от API "hh.ru" получено вакансий: {vacancies_count} '
                f'для региона: {region_code_hh} и населенного пункта: {location}'
            )
            vacansies = await self.parce_vacancies_hh(
                vacancies=vacansies_raw, location=location
            )
            return {
                'vacansies': vacansies,
                'vacancies_count': vacancies_count,
            }
        except HHAPIRequestError:
            raise

    async def get_vacancies_info(self, location: str, region_data: dict) -> dict:
        """
        Получает количество вакансий по заданному региону и населенному
        пункту.
        """
        logger.info(
            'Данные для поиска вакансий:'
            f'\n - location: {location}\n - region_data: {region_data}'
        )
        vacansies = []
        try:
            vacansies_hh = await self.get_vacancies_hh_api(
                location=location,
                region_code_hh=region_data.get('region_code_hh')
            )
            vacansies_tv = await self.get_vacancies_tv_api(
                location=location,
                region_code_tv=region_data.get('region_code_tv')
            )
            vacansies.extend(vacansies_hh.get('vacansies'))
            vacansies.extend(vacansies_tv.get('vacansies'))

            region_name = region_data.get('region_name')
            all_vacancies_count = len(vacansies)
            await self.vacancies_repository.delete_vacancies_by_location(
                location=location
            )
            await self.vacancies_repository.save_vacancies(
                vacancies=vacansies
            )
            logger.info(
                f'Сохранено {all_vacancies_count} вакансий в БД '
                f'для региона: {region_name} '
                f'и населенного пункта: {location}'
            )
            vacancies_count_tv = vacansies_tv.get('vacancies_count')
            vacancies_count_hh = vacansies_hh.get('vacancies_count')
            return {
                'all_vacancies_count': all_vacancies_count,
                'vacancies_count_tv': vacancies_count_tv,
                'vacancies_count_hh': vacancies_count_hh,
                'location': location,
                'region_name': region_name,
            }
        except (
            TVAPIRequestError,
            HHAPIRequestError,
            VacanciesHHNotFoundError,
            VacanciesTVNotFoundError,
            VacancyParseError,
            VacanciesRepositoryError
        ):
            raise

    async def get_vacancies_by_location(
        self, location: str, page: int, page_size: int
    ):
        """
        Возвращает список вакансий в локации по заданным условиям.
        """
        logger.info(
            f'Получение списка вакансий по локации: {location}, '
            f'страница: {page}, размер страницы: {page_size}'
        )
        try:
            total = await self.vacancies_repository.get_count_vacancies(
                location=location
            )
            if total == 0:
                logger.info(f'Вакансии не найдены для локации: {location}')
                raise VacanciesNotFoundError(location=location)
            vacancies = await self.vacancies_repository.get_vacancies(
                location=location, page=page, page_size=page_size
            )
            items = [
                VacancyOutSchema.model_validate(vacancy) for vacancy in vacancies
            ]
            return VacanciesListSchema(
                total=total,
                page=page,
                page_size=page_size,
                items=items
            )
        except VacanciesRepositoryError:
            raise

    async def get_vacancy_details_tv_api(self, vacancy_id: str, employer_code: str):
        """
        Возвращает информацию по вакансии от trudvsem.ru api по vacancy_id и employer_code.
        """
        try:
            vacancy_raw = await self.tv_client_api.get_one_vacancy(
                vacancy_id=vacancy_id,
                employer_code=employer_code
            )
            if not vacancy_raw:
                logger.info(
                    'Вакансия от API "Работа России" не найдена.'
                    f'vacancy_id={vacancy_id}, employer_code={employer_code}'
                )
                raise VacancyTVNotFoundError(
                    vacancy_id=vacancy_id, employer_code=employer_code
                )
            return await self.parce_vacancy_details_tv(
                vacancy=vacancy_raw
            )
        except (TVAPIRequestError, VacancyParseError):
            raise

    async def get_vacancy_details_hh_api(self, vacancy_id: str):
        """
        Возвращает информацию по вакансии от hh.ru api по vacancy_id.
        """
        try:
            vacancy_raw = await self.hh_client_api.get_one_vacancy(
                vacancy_id=vacancy_id
            )
            if not vacancy_raw:
                logger.info(
                    'Вакансия от API "Работа России" не найдена.'
                    f'vacancy_id={vacancy_id}'
                )
                raise VacancyHHNotFoundError(
                    vacancy_id=vacancy_id
                )
            return await self.parce_vacancy_details_hh(
                vacancy=vacancy_raw
            )
        except (HHAPIRequestError, VacancyParseError):
            raise

    async def get_vacancy_details(self, vacancy_id: str):
        """
        Возвращает информацию по вакансии по vacancy_id.
        """
        logger.info(
            f'Получение подробной информации по вакансии с vacancy_id={vacancy_id}, '
        )
        try:
            vacancy_raw = await self.vacancies_repository.get_vacancy_by_id(
                vacancy_id=vacancy_id
            )
            if not vacancy_raw:
                logger.info(f'Вакансия с vacancy_id={vacancy_id} не найдена в БД')
                raise VacancyNotFoundError(vacancy_id=vacancy_id)
            vacancy = VacancyOutSchema.model_validate(vacancy_raw)

            if vacancy.vacancy_source == 'hh.ru':
                vacancy_details_raw = await self.get_vacancy_details_hh_api(
                    vacancy_id=vacancy.vacancy_id
                )
            elif vacancy.vacancy_source == 'Работа России':
                vacancy_details_raw = await self.get_vacancy_details_tv_api(
                    vacancy_id=vacancy.vacancy_id,
                    employer_code=vacancy.employer_code
                )
            else:
                logger.info(
                    f'Неизвестный источник ({vacancy.vacancy_source}) для вакансии с vacancy_id={vacancy_id}.'
                )
                raise VacancyNotFoundError(vacancy_id=vacancy_id)
            logger.info(
                f'Детальная информация по вакансии с vacancy_id={vacancy_id} из '
                f'источника - {vacancy.vacancy_source}:\n{pformat(vacancy_details_raw)}'
            )
            try:
                vacancy_details1 = VacancyDetailsOutSchema.model_validate(vacancy_details_raw)
                return vacancy_details1
            except ValidationError as error:
                logger.error(f'Ошибка при валидации данных вакансии: {error}')
                raise VacancyParseError
        except (
            TVAPIRequestError,
            HHAPIRequestError,
            VacancyParseError,
            VacancyHHNotFoundError,
            VacancyTVNotFoundError,
        ):
            raise
