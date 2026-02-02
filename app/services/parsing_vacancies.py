import logging
import re
from pprint import pformat

from exceptions.parsing_vacancies import VacancyParseError

logger = logging.getLogger(__name__)


class VacanciesParsingService:
    """Сервис для парсинга и преобразования данных о вакансиях из различных источников."""

    DEFAULT_NOT_SPECIFIED = "Не указано"
    DEFAULT_DUTY = "Работодатель не указал должностные обязанности."
    DEFAULT_PHONE = "Работодатель не указал номер телефона"
    DEFAULT_EMAIL = "Работодатель не указал адрес электронной почты."
    DEFAULT_SALARY = "Работодатель не указал заработную плату."
    SOCIAL_PROTECTED = "Инвалиды"
    FIRST_ELEMENT_LIST = 0
    VACANCY_SOURCES = {
        "trudvsem": "Работа России",
        "hh": "hh.ru",
    }

    def parce_vacancy_details_tv(self, vacancy: dict) -> dict:
        """
        Обрабатывает и преобразует детальные данные одной вакансии от API Trudvsem.ru.

        Args:
            vacancy: Словарь с детальными данными о вакансии.

        Returns:
            Словарь с нормализованными данными вакансии.

        Raises:
            VacancyParseError: Если в процессе обработки данных возникает ошибка.
        """
        vacancy_id = vacancy.get("id")
        employer_code = vacancy.get("company", {}).get("companycode")

        logger.info(
            "Начинаю парсинг детальной информации для вакансии TV с ID: %s, company_code: %s",
            vacancy_id, employer_code
        )
        try:
            salary = vacancy.get("salary") or self.DEFAULT_SALARY
            employer_name = vacancy.get("company", {}).get("name")

            pars_vacancy_data = {
                "vacancy_name": vacancy.get("job-name"),
                "vacancy_id": vacancy_id,
                "status": "actual",
                "vacancy_url": vacancy.get("vac_url"),
                "social_protected": vacancy.get("social_protected"),
                "vacancy_source": "Работа России",
                "description": self._get_vacancy_duty_tv(vacancy=vacancy),
                "employer_location": self._get_employer_location_tv(vacancy=vacancy),
                "salary": salary,
                "employer_name": employer_name,
                "company_code": employer_code,
                "employer_phone": self._get_contact_phone_number_tv(vacancy=vacancy),
                "employer_email": self._get_contact_email_tv(vacancy=vacancy),
                "contact_person": vacancy.get("contact_person", self.DEFAULT_NOT_SPECIFIED),
                "employment": vacancy.get("employment", self.DEFAULT_NOT_SPECIFIED),
            }
            logger.info(
                "Результат парсинга вакансии TV с ID %s:\n%s",
                vacancy_id,
                pformat(pars_vacancy_data)
            )
            return pars_vacancy_data
        except Exception as error:
            logger.exception(
                'Ошибка при обработке вакансии от Trudvsem с ID %s: %s',
                vacancy_id,
                error
            )
            raise VacancyParseError(
                error_details="An error occurred while processing the vacancy data.",
                vacancy_id=vacancy_id,
                employer_code=employer_code,
                source="trudvsem.ru API",
            )

    def parce_vacancy_details_hh(self, vacancy: dict) -> dict:
        """
        Обрабатывает и преобразует детальные данные одной вакансии от API hh.ru.

        Args:
            vacancy: Словарь с детальными данными о вакансии.

        Returns:
            Словарь с нормализованными данными вакансии.

        Raises:
            VacancyParseError: Если в процессе обработки данных возникает ошибка.
        """
        vacancy_id = vacancy.get("id")
        logger.info(
            "Начинаю парсинг детальной информации для вакансии HH с ID: %s",
            vacancy_id
        )
        try:
            employer = vacancy.get("employer", {}) or {}
            employer_name = employer.get("name", self.DEFAULT_NOT_SPECIFIED)
            employer_code = employer.get("id", self.DEFAULT_NOT_SPECIFIED)

            contacts = vacancy.get("contacts", {}) or {}
            employer_email = contacts.get("email") or self.DEFAULT_EMAIL
            phones = contacts.get("phones", []) or []
            employer_phone = (
                phones[0].get("number")
                if phones and isinstance(phones[0], dict)
                else self.DEFAULT_PHONE
            )

            employment = (
                vacancy.get("employment", {}).get("name")
                if isinstance(vacancy.get("employment"), dict)
                else self.DEFAULT_NOT_SPECIFIED
            )
            parsed_vacancy = {
                "status": self._get_vacancy_status_hh(vacancy=vacancy),
                "vacancy_name": vacancy.get("name", self.DEFAULT_NOT_SPECIFIED),
                "vacancy_id": vacancy_id,
                "vacancy_url": vacancy.get("alternate_url"),
                "social_protected": self.SOCIAL_PROTECTED,
                "vacancy_source": "hh.ru",
                "description": self._get_vacancy_description_hh(vacancy=vacancy),
                "employer_location": self._get_employer_location_hh(vacancy=vacancy),
                "salary": self._get_vacancy_salary_hh(vacancy=vacancy),
                "employer_name": employer_name,
                "company_code": employer_code,
                "employer_phone": employer_phone,
                "employer_email": employer_email,
                "contact_person": self.DEFAULT_NOT_SPECIFIED,
                "employment": employment,
            }
            logger.info(
                "Результат парсинга вакансии HH с ID %s:\n%s",
                vacancy_id,
                pformat(parsed_vacancy)
            )
            return parsed_vacancy
        except Exception as error:
            logger.exception(
                "Ошибка при обработке вакансии от hh.ru с ID %s: %s",
                vacancy_id,
                error
            )
            raise VacancyParseError(
                error_details="An error occurred while processing the vacancy data.",
                vacancy_id=vacancy_id,
                employer_code=employer_code,
                source="HH.ru API",
            )

    def parce_vacancies_tv(self, vacancies: list[dict], location: str) -> list[dict]:
        """
        Обрабатывает и преобразует список вакансий от API Trudvsem.ru.

        Args:
            vacancies: Список словарей с данными вакансий.
            location: Наименование населенного пункта, для которого были найдены вакансии.

        Returns:
            Список словарей с нормализованными данными вакансий.

        Raises:
            VacancyParseError: Если в процессе обработки списка возникает ошибка.
        """
        logger.info(
            "Начинаю парсинг списка вакансий от Trudvsem для локации '%s'.",
            location
        )
        parsed_vacancies = []

        for vacancy_data in vacancies:
            try:
                vacancy: dict = vacancy_data.get("vacancy", {})

                vacancy_id = vacancy.get("id")

                experience = (
                    vacancy.get("requirement", {})
                    .get("education", self.DEFAULT_NOT_SPECIFIED)
                )
                category = (
                    vacancy.get("category", {}).get(
                        "specialisation", self.DEFAULT_NOT_SPECIFIED
                    )
                )
                salary = (
                    vacancy.get("salary") or self.DEFAULT_SALARY
                )
                employer_code = (
                    vacancy.get("company", {}).get("companycode")
                )
                employer_name = vacancy.get("company", {}).get("name")

                parsed_vacancies.append(
                {
                    "vacancy_id": vacancy_id,
                    "location": location,
                    "name": vacancy.get("job-name"),
                    "description": self._get_vacancy_duty_tv(vacancy=vacancy),
                    "salary": salary,
                    "vacancy_url": vacancy.get("vac_url"),
                    "vacancy_source": self.VACANCY_SOURCES.get("trudvsem"),
                    "employer_name": employer_name,
                    "employer_location": self._get_employer_location_tv(vacancy=vacancy),
                    "employer_phone": self._get_contact_phone_number_tv(vacancy=vacancy),
                    "employer_code": employer_code,
                    "experience_required": experience,
                    "category": category,
                    "employment_type": vacancy.get("employment") or self.DEFAULT_NOT_SPECIFIED,
                    "schedule": vacancy.get("schedule"),
                }
            )
            
            except Exception as error:
                logger.exception(
                    "Ошибка при обработке списка вакансий от Trudvsem для локации '%s': %s",
                    location,
                    error
                )
                raise VacancyParseError(
                    error_details="An error occurred while processing the vacancy list.",
                    vacancy_id=vacancy_id,
                    employer_code=employer_code,
                    source="trudvsem.ru API",
                )

        logger.info(
            "Обработано %d вакансий от Trudvsem для локации '%s'.",
            len(parsed_vacancies),
            location
        )
        return parsed_vacancies

    def parce_vacancies_hh(self, vacancies: list[dict], location: str) -> list[dict]:
        """
        Обрабатывает и преобразует список вакансий от API hh.ru.

        Args:
            vacancies: Список словарей с данными вакансий.
            location: Наименование населенного пункта, для которого были найдены вакансии.

        Returns:
            Список словарей с нормализованными данными вакансий.

        Raises:
            VacancyParseError: Если в процессе обработки списка возникает ошибка.
        """
        logger.info(
            "Начинаю парсинг списка вакансий от hh.ru для локации '%s'.",
            location
        )

        parsed_vacancies = []
        for vacancy in vacancies:
            try:
                vacancy_id = vacancy.get("id")
                employer_code = (
                    vacancy.get("employer", {})
                    .get("id", self.DEFAULT_NOT_SPECIFIED)
                )
                experience_required = (
                    vacancy.get("experience", {})
                    .get("name", self.DEFAULT_NOT_SPECIFIED)
                )
                category = (
                    vacancy.get("professional_roles", [{}])[self.FIRST_ELEMENT_LIST]
                    .get("name", self.DEFAULT_NOT_SPECIFIED)
                )
                employment_type = (
                    vacancy.get("employment", {})
                    .get("name", self.DEFAULT_NOT_SPECIFIED)
                )
                schedule = (
                    vacancy.get("schedule", {})
                    .get("name", self.DEFAULT_NOT_SPECIFIED)
                )
                parsed_vacancies.append(
                    {
                        "vacancy_id": vacancy_id,
                        "location": location,
                        "name": vacancy.get("name"),
                        "description": self._get_many_vacancies_description_hh(vacancy=vacancy),
                        "salary": self._get_vacancy_salary_hh(vacancy=vacancy),
                        "vacancy_url": vacancy.get("alternate_url"),
                        'vacancy_source': self.VACANCY_SOURCES.get("hh"),
                        "employer_name": self._get_employer_name_hh(vacancy=vacancy),
                        "employer_location": self._get_employer_location_hh(
                            vacancy=vacancy, location=location
                        ),
                        "employer_phone": self._get_contact_phone_number_hh(vacancy=vacancy),
                        "employer_code": employer_code,
                        "experience_required": experience_required,
                        "category": category,
                        'employment_type': employment_type,
                        "schedule": schedule,
                    }
                )
            except Exception as error:
                logger.exception(
                    "Ошибка при обработке списка вакансий от hh.ru для локации '%s': %s",
                    location,
                    error
                )
                raise VacancyParseError(
                    error_details="An error occurred while processing the vacancy list.",
                    vacancy_id=vacancy_id,
                    employer_code=employer_code,
                    source="HH.ru API",
                )
        
        logger.info(
            "Обработано %d вакансий от hh.ru для локации '%s'.",
            len(parsed_vacancies),
            location
        )
        return parsed_vacancies
    
    def _get_vacancy_duty_tv(self, vacancy: dict) -> str:
        """Извлекает и очищает описание должностных обязанностей из данных Trudvsem."""
        duty_raw = vacancy.get("duty")
        if duty_raw:
            duty = (
                re.sub(r"<[^>]+>", "", duty_raw, flags=re.S)
                .replace("&nbsp;", "")
                .replace("&nbsp", "")
            )
        else:
            duty = self.DEFAULT_DUTY

        return duty

    def _get_contact_phone_number_tv(self, vacancy: dict) -> str:
        """Извлекает контактный номер телефона из данных Trudvsem."""
        contact_list: list[dict] = vacancy.get("contact_list") or []
        contact_phone_number = next(
            (
                c["contact_value"] for c in contact_list if c.get("contact_type") == "Телефон"
            ), self.DEFAULT_PHONE
        )

        return contact_phone_number

    def _get_contact_email_tv(self, vacancy: dict) -> str:
        """Извлекает контактный email из данных Trudvsem."""
        contact_list: list[dict] = vacancy.get("contact_list") or []

        contact_email = next(
            (
                c["contact_value"] for c in contact_list if c.get("contact_type") == "Эл. почта"
            ), self.DEFAULT_EMAIL
        )

        return contact_email

    def _get_employer_location_tv(self, vacancy: dict) -> str:
        """Извлекает местоположение работодателя из данных Trudvsem."""
        addresses = (
            vacancy.get("addresses", {}).get("address", [])
        )

        vacancy_location = (
            (addresses[0] or {}).get("location")
            if addresses else self.DEFAULT_NOT_SPECIFIED
        ) or self.DEFAULT_NOT_SPECIFIED

        return vacancy_location

    def _get_vacancy_status_hh(self, vacancy: dict) -> str:
        """Определяет статус вакансии hh.ru (актуальная или архивная)."""
        archived = vacancy.get('archived')
        if archived:
            logger.info("Вакнасия с vacancy_id=%s перенесаперенесена в архив", vacancy.get("id"))
            return "archival"
        return "actual"

    def _get_vacancy_salary_hh(self, vacancy: dict) -> str:
        """Форматирует информацию о заработной плате из данных hh.ru."""
        salary_info = vacancy.get("salary") or {}
        salary_from = salary_info.get("from")
        salary_to = salary_info.get("to")

        if not salary_info:
            salary = self.DEFAULT_SALARY
        elif salary_from and salary_to:
            salary = f"от {salary_from} до {salary_to}"
        elif salary_from:
            salary = f"от {salary_from}"
        elif salary_to:
            salary = f"до {salary_to}"
        else:
            salary = self.DEFAULT_SALARY

        return salary

    def _get_vacancy_description_hh(self, vacancy: dict) -> str:
        """Извлекает и очищает описание вакансии из детальных данных hh.ru."""
        description_raw = vacancy.get("description", "") or ""
        description = re.sub(
            r"<[^>]+>", "", description_raw, flags=re.S
        ) or self.DEFAULT_NOT_SPECIFIED

        return description

    def _get_employer_location_hh(self, vacancy: dict, location: str = "") ->str:
        """Извлекает местоположение работодателя из данных hh.ru."""
        address = vacancy.get("address", {}) or {}
        employer_location = (
            address.get("raw") if address
            else vacancy.get("area", {}).get("name", location)
        ) or self.DEFAULT_NOT_SPECIFIED

        return employer_location

    def _get_contact_phone_number_hh(self, vacancy: dict) -> str:
        """Извлекает контактный номер телефона из данных hh.ru."""
        contacts = vacancy.get("contacts") or {}
        phones = contacts.get("phones") or []
        if phones and phones[self.FIRST_ELEMENT_LIST].get("formatted"):
            employer_phone_number = phones[self.FIRST_ELEMENT_LIST]["formatted"]
        else:
            employer_phone_number = self.DEFAULT_PHONE

        return employer_phone_number
    
    def _get_employer_name_hh(self, vacancy: dict) -> str:
        """Извлекает и очищает название работодателя из данных hh.ru."""
        employer_name: str = vacancy.get("employer", {}).get("name", "")
        employer_name = (
            (
                employer_name.replace("Job development", "").replace("(", "").replace(")", "")
            ) or self.DEFAULT_NOT_SPECIFIED
        )
        return employer_name

    def _get_many_vacancies_description_hh(self, vacancy: dict) -> str:
        """Формирует краткое описание вакансии из данных hh.ru для списков."""
        description = ""
        snippet: dict = vacancy.get("snippet", {})
        if snippet.get("responsibility"):
            description += snippet["responsibility"]
        if snippet.get("requirement"):
            description += "\n\nТребования: " + snippet["requirement"]
                
        return description.strip()
