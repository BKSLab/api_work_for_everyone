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
        "trudvsem": "trudvsem.ru",
        "hh": "hh.ru",
    }

    def parse_vacancy_details_tv(self, vacancy: dict) -> dict:
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
            "📦 Парсинг детальной информации вакансии trudvsem.ru. ID: %s, код компании: %s",
            vacancy_id, employer_code
        )
        try:
            salary = vacancy.get("salary") or self.DEFAULT_SALARY
            employer_name = vacancy.get("company", {}).get("name")

            requirement = vacancy.get("requirement") or {}
            experience_required = requirement.get("education", self.DEFAULT_NOT_SPECIFIED)
            requirements = vacancy.get("requirements", self.DEFAULT_NOT_SPECIFIED) or self.DEFAULT_NOT_SPECIFIED

            pars_vacancy_data = {
                "vacancy_id": vacancy_id,
                "vacancy_name": vacancy.get("job-name"),
                "location": self.DEFAULT_NOT_SPECIFIED,
                "status": "actual",
                "vacancy_url": vacancy.get("vac_url"),
                "vacancy_source": self.VACANCY_SOURCES.get("trudvsem"),
                "description": self._get_vacancy_duty_tv(vacancy=vacancy),
                "salary": salary,
                "employer_name": employer_name,
                "employer_location": self._get_employer_location_tv(vacancy=vacancy),
                "employer_phone": self._get_contact_phone_number_tv(vacancy=vacancy),
                "employer_code": employer_code,
                "employer_email": self._get_contact_email_tv(vacancy=vacancy),
                "contact_person": vacancy.get("contact_person", self.DEFAULT_NOT_SPECIFIED),
                "employment": vacancy.get("employment", self.DEFAULT_NOT_SPECIFIED),
                "schedule": vacancy.get("schedule", self.DEFAULT_NOT_SPECIFIED),
                "work_format": self.DEFAULT_NOT_SPECIFIED,
                "experience_required": experience_required,
                "requirements": requirements,
                "category": vacancy.get("category", {}).get("specialisation", self.DEFAULT_NOT_SPECIFIED),
                "social_protected": vacancy.get("social_protected", self.DEFAULT_NOT_SPECIFIED),
            }
            pars_vacancy_data = self._sanitize_vacancy(pars_vacancy_data)
            logger.info(
                "✅ Вакансия trudvsem.ru распарсена. ID: %s:\n%s",
                vacancy_id,
                pformat(pars_vacancy_data)
            )
            return pars_vacancy_data
        except Exception as error:
            logger.exception(
                "❌ Ошибка парсинга вакансии trudvsem.ru. ID: %s. Детали: %s",
                vacancy_id,
                error
            )
            raise VacancyParseError(
                error_details="Ошибка при обработке данных вакансии.",
                vacancy_id=vacancy_id,
                employer_code=employer_code,
                source="trudvsem.ru API",
            )

    def parse_vacancy_details_hh(self, vacancy: dict) -> dict:
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
            "📦 Парсинг детальной информации вакансии hh.ru. ID: %s",
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
                vacancy.get("employment_form", {}).get("name")
                if isinstance(vacancy.get("employment_form"), dict)
                else self.DEFAULT_NOT_SPECIFIED
            )
            experience_required = (
                vacancy.get("experience", {}).get("name", self.DEFAULT_NOT_SPECIFIED)
                if isinstance(vacancy.get("experience"), dict)
                else self.DEFAULT_NOT_SPECIFIED
            )
            key_skills = vacancy.get("key_skills") or []
            requirements = (
                ", ".join(s.get("name", "") for s in key_skills if s.get("name"))
                or self.DEFAULT_NOT_SPECIFIED
            )
            work_format_list = vacancy.get("work_format") or []
            work_format = (
                ", ".join(wf.get("name", "") for wf in work_format_list if wf.get("name"))
                or self.DEFAULT_NOT_SPECIFIED
            )
            category = (
                vacancy.get("professional_roles", [{}])[self.FIRST_ELEMENT_LIST]
                .get("name", self.DEFAULT_NOT_SPECIFIED)
                if vacancy.get("professional_roles") else self.DEFAULT_NOT_SPECIFIED
            )
            parsed_vacancy = {
                "vacancy_id": vacancy_id,
                "vacancy_name": vacancy.get("name", self.DEFAULT_NOT_SPECIFIED),
                "location": vacancy.get("area", {}).get("name", self.DEFAULT_NOT_SPECIFIED),
                "status": self._get_vacancy_status_hh(vacancy=vacancy),
                "vacancy_url": vacancy.get("alternate_url"),
                "vacancy_source": self.VACANCY_SOURCES.get("hh"),
                "description": self._get_vacancy_description_hh(vacancy=vacancy),
                "salary": self._get_vacancy_salary_hh(vacancy=vacancy),
                "employer_name": employer_name,
                "employer_location": self._get_employer_location_hh(vacancy=vacancy),
                "employer_phone": employer_phone,
                "employer_code": employer_code,
                "employer_email": employer_email,
                "contact_person": self.DEFAULT_NOT_SPECIFIED,
                "employment": employment,
                "schedule": self.DEFAULT_NOT_SPECIFIED,
                "work_format": work_format,
                "experience_required": experience_required,
                "requirements": requirements,
                "category": category,
                "social_protected": self.SOCIAL_PROTECTED,
            }
            parsed_vacancy = self._sanitize_vacancy(parsed_vacancy)
            logger.info(
                "✅ Вакансия hh.ru распарсена. ID: %s:\n%s",
                vacancy_id,
                pformat(parsed_vacancy)
            )
            return parsed_vacancy
        except Exception as error:
            logger.exception(
                "❌ Ошибка парсинга вакансии hh.ru. ID: %s. Детали: %s",
                vacancy_id,
                error
            )
            raise VacancyParseError(
                error_details="Ошибка при обработке данных вакансии.",
                vacancy_id=vacancy_id,
                employer_code=employer_code,
                source="HH.ru API",
            )

    def parse_vacancies_tv(self, vacancies: list[dict], location: str) -> list[dict]:
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
            "📦 Парсинг списка вакансий trudvsem.ru. Населённый пункт: '%s'.",
            location
        )
        parsed_vacancies = []

        pattern = rf"(?i)\b{location}\b"

        for vacancy_data in vacancies:
            try:
                vacancy: dict = vacancy_data.get("vacancy", {})

                vacancy_location = self._get_employer_location_tv(vacancy=vacancy)
                
                # фильтруем по локации
                if not re.search(pattern, vacancy_location):
                    continue

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
                raw_salary = vacancy.get("salary")
                salary = str(raw_salary)[:295] if raw_salary is not None else self.DEFAULT_SALARY
                employer_code = (
                    vacancy.get("company", {}).get("companycode")
                )
                employer_name = vacancy.get("company", {}).get("name")

                parsed_vacancies.append(
                self._sanitize_vacancy({
                    "vacancy_id": str(vacancy_id) if vacancy_id is not None else self.DEFAULT_NOT_SPECIFIED,
                    "location": location,
                    "vacancy_name": vacancy.get("job-name") or self.DEFAULT_NOT_SPECIFIED,
                    "status": "actual",
                    "description": self._get_vacancy_duty_tv(vacancy=vacancy),
                    "salary": salary,
                    "vacancy_url": vacancy.get("vac_url") or self.DEFAULT_NOT_SPECIFIED,
                    "vacancy_source": self.VACANCY_SOURCES.get("trudvsem"),
                    "employer_name": employer_name or self.DEFAULT_NOT_SPECIFIED,
                    "employer_location": vacancy_location,
                    "employer_phone": self._get_contact_phone_number_tv(vacancy=vacancy),
                    "employer_code": str(employer_code) if employer_code is not None else self.DEFAULT_NOT_SPECIFIED,
                    "employer_email": self._get_contact_email_tv(vacancy=vacancy),
                    "contact_person": vacancy.get("contact_person", self.DEFAULT_NOT_SPECIFIED),
                    "employment": vacancy.get("employment") or self.DEFAULT_NOT_SPECIFIED,
                    "schedule": vacancy.get("schedule") or self.DEFAULT_NOT_SPECIFIED,
                    "work_format": self.DEFAULT_NOT_SPECIFIED,
                    "experience_required": experience,
                    "requirements": vacancy.get("requirements", self.DEFAULT_NOT_SPECIFIED) or self.DEFAULT_NOT_SPECIFIED,
                    "category": category,
                    "social_protected": vacancy.get("social_protected", self.DEFAULT_NOT_SPECIFIED),
                })
            )
            
            except Exception as error:
                logger.exception(
                    "❌ Ошибка парсинга списка вакансий trudvsem.ru. Населённый пункт: '%s'. Детали: %s",
                    location,
                    error
                )
                raise VacancyParseError(
                    error_details="Ошибка при обработке списка вакансий.",
                    vacancy_id=vacancy_id,
                    employer_code=employer_code,
                    source="trudvsem.ru API",
                )

        logger.info(
            "✅ Парсинг завершён (trudvsem.ru). Обработано вакансий: %d. Населённый пункт: '%s'.",
            len(parsed_vacancies),
            location
        )
        return parsed_vacancies

    def parse_vacancies_hh(self, vacancies: list[dict], location: str) -> list[dict]:
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
            "📦 Парсинг списка вакансий hh.ru. Населённый пункт: '%s'.",
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
                employment = (
                    vacancy.get("employment_form", {}).get("name", self.DEFAULT_NOT_SPECIFIED)
                    if isinstance(vacancy.get("employment_form"), dict)
                    else self.DEFAULT_NOT_SPECIFIED
                )
                work_format_list = vacancy.get("work_format") or []
                work_format = (
                    ", ".join(wf.get("name", "") for wf in work_format_list if wf.get("name"))
                    or self.DEFAULT_NOT_SPECIFIED
                )
                contacts = vacancy.get("contacts") or {}
                employer_email = contacts.get("email") or self.DEFAULT_EMAIL
                parsed_vacancies.append(
                    self._sanitize_vacancy({
                        "vacancy_id": str(vacancy_id) if vacancy_id is not None else self.DEFAULT_NOT_SPECIFIED,
                        "location": location,
                        "vacancy_name": vacancy.get("name") or self.DEFAULT_NOT_SPECIFIED,
                        "status": "archival" if vacancy.get("archived") else "actual",
                        "description": self._get_many_vacancies_description_hh(vacancy=vacancy) or self.DEFAULT_NOT_SPECIFIED,
                        "salary": self._get_vacancy_salary_hh(vacancy=vacancy),
                        "vacancy_url": vacancy.get("alternate_url") or self.DEFAULT_NOT_SPECIFIED,
                        "vacancy_source": self.VACANCY_SOURCES.get("hh"),
                        "employer_name": self._get_employer_name_hh(vacancy=vacancy),
                        "employer_location": self._get_employer_location_hh(
                            vacancy=vacancy, location=location
                        ),
                        "employer_phone": self._get_contact_phone_number_hh(vacancy=vacancy),
                        "employer_code": str(employer_code) if employer_code is not None else self.DEFAULT_NOT_SPECIFIED,
                        "employer_email": employer_email,
                        "contact_person": self.DEFAULT_NOT_SPECIFIED,
                        "employment": employment,
                        "schedule": self.DEFAULT_NOT_SPECIFIED,
                        "work_format": work_format,
                        "experience_required": experience_required,
                        "requirements": self.DEFAULT_NOT_SPECIFIED,
                        "category": category,
                        "social_protected": self.SOCIAL_PROTECTED,
                    })
                )
            except Exception as error:
                logger.exception(
                    "❌ Ошибка парсинга списка вакансий hh.ru. Населённый пункт: '%s'. Детали: %s",
                    location,
                    error
                )
                raise VacancyParseError(
                    error_details="Ошибка при обработке списка вакансий.",
                    vacancy_id=vacancy_id,
                    employer_code=employer_code,
                    source="HH.ru API",
                )
        
        logger.info(
            "✅ Парсинг завершён (hh.ru). Обработано вакансий: %d. Населённый пункт: '%s'.",
            len(parsed_vacancies),
            location
        )
        return parsed_vacancies
    
    @staticmethod
    def _sanitize_vacancy(vacancy: dict) -> dict:
        """Очищает строковые поля вакансии от символов, недопустимых в PostgreSQL."""
        return {
            key: value.replace("\x00", "").replace("\xa0", " ")
            if isinstance(value, str) else value
            for key, value in vacancy.items()
        }

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
            logger.info("⚠️ Вакансия hh.ru перенесена в архив. ID: %s", vacancy.get("id"))
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
