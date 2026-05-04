import asyncio
import functools
import logging
import re
from datetime import datetime, timedelta, timezone
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
from repositories.assistant_session import AssistantSessionRepository
from repositories.favorite_event import FavoriteEventRepository
from repositories.favorites import FavoritesRepository
from repositories.search_event import SearchEventRepository
from repositories.vacancies import VacanciesRepository
from schemas.vacancies import (
    FavoriteVacanciesListSchema,
    VacanciesListSchema,
    VacancySchema,
)
from schemas.vacancy_assistant import QuestionnaireResponseSchema
from services.parsing_vacancies import VacanciesParsingService
from services.regions import RegionService
from services.vacancy_assistant import VacancyAiAssistant

logger = logging.getLogger(__name__)


class VacanciesService:
    """Сервис для управления бизнес-логикой, связанной с вакансиями."""
    MAX_COUNT_PARTS_IN_LOCATION = 3
    FLAG_VACANCY_NOT_FOUND = "not_found"
    SEMAPHORE_LIMIT = 5
    FAVORITES_TTL_HOURS = 24
    VACANCIES_TTL_HOURS = 1

    def __init__(
        self,
        region_service: RegionService,
        vacancies_repository: VacanciesRepository,
        favorites_repository: FavoritesRepository,
        favorite_event_repository: FavoriteEventRepository,
        assistant_session_repository: AssistantSessionRepository,
        search_event_repository: SearchEventRepository,
        hh_client_api: HHClient,
        tv_client_api: TVClient,
        vacancies_parser: VacanciesParsingService,
        vacancy_ai_assistant: VacancyAiAssistant,
    ):
        self.region_service = region_service
        self.vacancies_repository = vacancies_repository
        self.favorites_repository = favorites_repository
        self.favorite_event_repository = favorite_event_repository
        self.assistant_session_repository = assistant_session_repository
        self.search_event_repository = search_event_repository
        self.hh_client_api = hh_client_api
        self.tv_client_api = tv_client_api
        self.vacancies_parser = vacancies_parser
        self.vacancy_ai_assistant = vacancy_ai_assistant
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
            "🔍 Данные для валидации. Код региона: %s, населённый пункт: %s",
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
        logger.info("✅ Данные после валидации: %s", pformat(validated_data))
        return validated_data

    async def _is_vacancies_cache_valid(self, location: str) -> bool:
        """Возвращает True, если кэш вакансий по локации актуален и пригоден для использования.

        Кэш считается валидным, если данные моложе VACANCIES_TTL_HOURS
        и предыдущий запрос завершился без ошибок по всем источникам.
        """
        last_updated_at = await self.vacancies_repository.get_last_updated_at(location=location)
        if last_updated_at is None:
            logger.info("🔄 Вакансии по локации '%s' отсутствуют в БД. Запускаем сбор.", location)
            return False

        ttl_threshold = datetime.now(timezone.utc) - timedelta(hours=self.VACANCIES_TTL_HOURS)
        if last_updated_at < ttl_threshold:
            logger.info(
                "🔄 Вакансии по локации '%s' устарели (обновлено: %s, TTL: %dч). Запускаем сбор.",
                location, last_updated_at.strftime("%H:%M:%S %d.%m.%Y"), self.VACANCIES_TTL_HOURS,
            )
            return False

        error_hh_last, error_tv_last = await self.search_event_repository.get_last_error_flags(
            location=location
        )
        if error_hh_last or error_tv_last:
            logger.info(
                "⚠️ Данные по локации '%s' свежие, но предыдущий запрос завершился с ошибками "
                "(hh.ru: %s, trudvsem.ru: %s). Повторяем сбор из источников.",
                location, error_hh_last, error_tv_last,
            )
            return False

        return True

    async def get_vacancies_info(self, location: str, region_data: dict) -> dict:
        """
        Инициирует поиск, сбор, сохранение и возврат вакансий.

        Если данные по локации свежие (< VACANCIES_TTL_HOURS), возвращает счётчики
        из БД без обращения к внешним API. Иначе — выполняет полный сбор из источников,
        сохраняет в БД и возвращает результат.

        Args:
            location: Нормализованное наименование населенного пункта.
            region_data: Словарь с данными о регионе.

        Returns:
            Словарь с результатами поиска, включая счётчики вакансий и флаги ошибок.

        Raises:
            VacanciesServiceError: Если не удалось получить данные ни из одного источника.
        """
        logger.info(
            "🔍 Данные для поиска вакансий. Регион: %s, населённый пункт: %s",
            pformat(region_data), location
        )

        region_name = region_data.get("name")

        if await self._is_vacancies_cache_valid(location=location):
            logger.info(
                "✅ Вакансии по локации '%s' свежие (<%dч). Возвращаем из БД.",
                location, self.VACANCIES_TTL_HOURS
            )
            total, counts_by_source = await asyncio.gather(
                self.vacancies_repository.get_count_vacancies(location=location),
                self.vacancies_repository.get_count_vacancies_by_source(location=location),
            )
            await self.search_event_repository.save_event({
                "location": location,
                "region_name": region_name,
                "region_code": region_data.get("code_tv", ""),
                "count_hh": counts_by_source.get("hh.ru", 0),
                "count_tv": counts_by_source.get("trudvsem.ru", 0),
                "total_count": total,
                "error_hh": False,
                "error_tv": False,
            })
            return {
                "all_vacancies_count": total,
                "vacancies_count_hh": counts_by_source.get("hh.ru", 0),
                "vacancies_count_tv": counts_by_source.get("trudvsem.ru", 0),
                "error_request_hh": False,
                "error_request_tv": False,
                "error_details_hh": "",
                "error_details_tv": "",
                "location": location,
                "region_name": region_name,
            }

        api_vacancies_response = await self._get_vacancies_data_from_apis(
            location=location, region_data=region_data
        )

        error_request_hh = api_vacancies_response.get("error_request_hh")
        error_request_tv = api_vacancies_response.get("error_request_tv")
        all_vacancies_count = api_vacancies_response.get("all_vacancies_count")

        if error_request_hh and error_request_tv:
            logger.error("❌ Не удалось получить данные вакансий ни из одного источника")
            raise VacanciesServiceError(
                error_details="Не удалось получить данные вакансий ни из одного источника."
            )

        await self._save_vacancies_data(
            all_vacancies_count=all_vacancies_count,
            location=location,
            vacancies=api_vacancies_response.get("vacancies"),
        )

        await self.search_event_repository.save_event({
            "location": location,
            "region_name": region_name,
            "region_code": region_data.get("code_tv", ""),
            "count_hh": api_vacancies_response.get("vacancies_count_hh", 0),
            "count_tv": api_vacancies_response.get("vacancies_count_tv", 0),
            "total_count": all_vacancies_count,
            "error_hh": bool(error_request_hh),
            "error_tv": bool(error_request_tv),
        })

        logger.info(
            "✅ Поиск вакансий завершён. Населённый пункт: '%s', регион: '%s'. Найдено: %d вакансий.",
            location, region_name, all_vacancies_count
        )

        api_vacancies_response.update({"location": location, "region_name": region_name})

        return api_vacancies_response

    async def get_vacancies_by_location(
        self,
        location: str,
        page: int,
        page_size: int,
        user_id: str | None = None,
        keyword: str | None = None,
        source: str | None = None,
    ):
        """
        Возвращает пагинированный список вакансий для указанной локации.

        Args:
            location: Наименование населенного пункта.
            user_id: Идентификатор пользователя во внешней системе, опциональное поле.
            page: Номер страницы.
            page_size: Количество элементов на странице.
            keyword: Ключевое слово для поиска в названии и описании вакансии.
            source: Фильтр по источнику ('hh.ru' или 'trudvsem.ru').

        Returns:
            Объект `VacanciesListSchema` с пагинированным списком вакансий.

        Raises:
            VacanciesServiceError: В случае ошибки валидации данных.
        """
        logger.info(
            "📋 Получение списка вакансий. Населённый пункт: %s, страница: %s, размер: %s, ключевое слово: %s, источник: %s",
            location, page, page_size, keyword, source
        )

        total, counts_by_source = await asyncio.gather(
            self.vacancies_repository.get_count_vacancies(
                location=location, keyword=keyword, source=source
            ),
            self.vacancies_repository.get_count_vacancies_by_source(
                location=location, keyword=keyword, source=source
            ),
        )
        if total == 0:
            items = []
        else:
            vacancies = await self.vacancies_repository.get_vacancies(
                location=location, page=page, page_size=page_size,
                keyword=keyword, source=source,
            )

            try:
                items = [
                    VacancySchema.model_validate(vacancy) for vacancy in vacancies
                ]
                # Если пользователь авторизован — проверяем избранное одним запросом
                if user_id:
                    vacancy_ids = [item.vacancy_id for item in items]
                    favorite_ids = await self.favorites_repository.get_favorite_vacancy_ids(
                        user_id, vacancy_ids
                    )
                    for item in items:
                        item.is_favorite = item.vacancy_id in favorite_ids

            except ValidationError as error:
                raise VacanciesServiceError(
                    error_details="Ошибка валидации данных при получении списка вакансий."
                ) from error

        logger.info(
            "✅ Вакансии получены. Населённый пункт: %s, страница: %s, размер: %s, найдено: %s.",
            location, page, page_size, len(items)
        )

        return VacanciesListSchema(
            total=total,
            page=page,
            page_size=page_size,
            vacancies_count_hh=counts_by_source.get("hh.ru", 0),
            vacancies_count_tv=counts_by_source.get("trudvsem.ru", 0),
            items=items
        )

    async def get_vacancy_details(self, vacancy_id: str, user_id: str | None = None) -> VacancySchema:
        """
        Возвращает детальную информацию по вакансии с учётом избранного пользователя.

        Для вакансий hh.ru всегда запрашивает актуальные данные из API,
        так как в БД хранится только краткое описание из листинга.
        Для trudvsem.ru данные берутся из БД (там уже полные данные).

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя для проверки избранного (опционально).

        Returns:
            Объект `VacancySchema` с детальной информацией о вакансии.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена в БД или во внешнем источнике.
            VacanciesServiceError: В случае ошибки валидации данных.
        """
        vacancy = await self._get_vacancy_by_id(vacancy_id=vacancy_id)

        try:
            detailed = await self._fetch_vacancy_details_from_api(
                vacancy_id=vacancy_id,
                vacancy_source=vacancy.vacancy_source,
                employer_code=vacancy.employer_code,
            )
            vacancy = VacancySchema(**detailed)
        except (VacancyNotFoundError, HHAPIRequestError, TVAPIRequestError, VacanciesServiceError) as error:
            logger.warning(
                "⚠️ Не удалось получить детали для ID %s: %s. Возвращаем данные из БД.",
                vacancy_id, error
            )

        if user_id:
            favorite_ids = await self.favorites_repository.get_favorite_vacancy_ids(
                user_id, [vacancy_id]
            )
            vacancy.is_favorite = vacancy_id in favorite_ids

        return vacancy

    async def add_vacancy_to_favorites(self, vacancy_id: str, user_id: str) -> None:
        """
        Добавляет вакансию в список избранного для пользователя.

        Для вакансий hh.ru дополнительно запрашивает детальную информацию
        из API, чтобы сохранить полное описание вместо короткого сниппета.

        Args:
            vacancy_id: Идентификатор вакансии для добавления.
            user_id: Идентификатор пользователя.
        """
        logger.info(
            "➕ Запрос на добавление вакансии в избранное. ID вакансии: %s, ID пользователя: %s",
            vacancy_id, user_id
        )

        vacancy = await self._get_vacancy_by_id(vacancy_id=vacancy_id)

        try:
            vacancy_dict = vacancy.model_dump()
            vacancy_dict.pop("is_favorite", None)
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="Ошибка валидации данных при получении информации о вакансии."
            ) from error

        try:
            detailed = await self._fetch_vacancy_details_from_api(
                vacancy_id=vacancy_id,
                vacancy_source=vacancy.vacancy_source,
                employer_code=vacancy.employer_code,
            )
            vacancy_dict.update(detailed)
        except (VacancyNotFoundError, HHAPIRequestError, TVAPIRequestError, VacanciesServiceError) as error:
            logger.warning(
                "⚠️ Не удалось получить детальную информацию для ID %s: %s. Сохраняем данные из БД.",
                vacancy_id, error
            )

        await self.favorites_repository.add_vacancy(
            favorite_data={"user_id": user_id, **vacancy_dict}
        )

        await self.favorite_event_repository.save_event({
            "user_id": user_id,
            "vacancy_id": vacancy_id,
            "action": "add",
            "vacancy_name": vacancy_dict.get("vacancy_name"),
            "employer_name": vacancy_dict.get("employer_name"),
            "vacancy_source": vacancy_dict.get("vacancy_source"),
            "location": vacancy_dict.get("location"),
            "category": vacancy_dict.get("category"),
            "salary": vacancy_dict.get("salary"),
            "description": vacancy_dict.get("description"),
        })
    
    async def delete_vacancy_from_favorites(self, vacancy_id: str, user_id: str) -> None:
        """
        Удаляет вакансию из списка избранного пользователя.

        Args:
            vacancy_id: Идентификатор вакансии для удаления.
            user_id: Идентификатор пользователя.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена в избранном у пользователя.
        """
        logger.info(
            "🗑️ Запрос на удаление вакансии из избранного. ID вакансии: %s, ID пользователя: %s",
            vacancy_id, user_id
        )
        favorite = await self.favorites_repository.get_vacancy_by_id(
            vacancy_id=vacancy_id, user_id=user_id
        )
        delete_result = await self.favorites_repository.delete_vacancy(
            user_id=user_id, vacancy_id=vacancy_id,
        )
        if not delete_result:
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Указанная вакансия не найдена в избранном пользователя."
            )

        if favorite:
            await self.favorite_event_repository.save_event({
                "user_id": user_id,
                "vacancy_id": vacancy_id,
                "action": "remove",
                "vacancy_name": favorite.vacancy_name,
                "employer_name": favorite.employer_name,
                "vacancy_source": favorite.vacancy_source,
                "location": favorite.location,
                "category": favorite.category,
                "salary": favorite.salary,
                "description": favorite.description,
            })

    async def get_user_favorites(self, user_id: str, page: int, page_size: int) -> FavoriteVacanciesListSchema:
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
            "📋 Получение избранных вакансий. ID пользователя: %s, страница: %s, размер: %s",
            user_id, page, page_size
        )

        total = await self.favorites_repository.get_count_favorites_vacancies(
            user_id=user_id
        )
        if total == 0:
            return FavoriteVacanciesListSchema(
                total=0, page=page, page_size=page_size, items=[]
            )

        logger.info("✅ Найдено вакансий в избранном у пользователя %s: %s.", user_id, total)
        vacancies_raw = await self.favorites_repository.get_favorites_vacancies(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        compiled_vacancies = await self._compile_enriched_favorite_vacancies(
            vacancies_raw=vacancies_raw
        )

        try:
            items = [
                VacancySchema.model_validate(vacancy) for vacancy in compiled_vacancies
            ]
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="Ошибка валидации данных при получении списка избранных вакансий."
            ) from error

        return FavoriteVacanciesListSchema(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    async def get_vacancy_by_id_from_favorites(self, vacancy_id: str, user_id: str | None) -> VacancySchema:
        """
        Возвращает актуальную детальную информацию по вакансии из избранного.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя. Если указан — ищет вакансию только
                     среди избранного этого пользователя. Если None — среди всех записей.

        Returns:
            Объект `VacancySchema` с детальной информацией о вакансии.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена в избранном или во внешнем источнике.
            VacanciesServiceError: При ошибке валидации или неизвестном источнике.
        """
        return await self._get_vacancy_by_id_from_favorites(
            vacancy_id=vacancy_id, user_id=user_id
        )

    # Блок методов AI-ассистента
    async def gen_cover_letter_by_vacancy(self, vacancy_id: str, user_id: str | None = None) -> str:
        """Генерирует шаблон сопроводительного письма по данным вакансии.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя для поиска вакансии в избранном.

        Returns:
            HTML-строка с советом и шаблоном сопроводительного письма.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена.
            VacanciesServiceError: При ошибке валидации данных.
        """
        logger.info("🤖 Генерация шаблона письма. ID вакансии: %s.", vacancy_id)
        vacancy = await self._get_vacancy_by_id_from_favorites(vacancy_id=vacancy_id, user_id=user_id)
        vacancy_dict = vacancy.model_dump()
        cover_letter = await self.vacancy_ai_assistant.gen_cover_letter_by_vacancy(
            vacancy=vacancy_dict
        )
        await self.assistant_session_repository.save_session(
            session_type="cover_letter_by_vacancy",
            vacancy_id=vacancy_id,
            vacancy_name=vacancy_dict.get("vacancy_name", ""),
            employer_name=vacancy_dict.get("employer_name"),
            employer_location=vacancy_dict.get("employer_location"),
            employment=vacancy_dict.get("employment"),
            salary=vacancy_dict.get("salary"),
            description=vacancy_dict.get("description"),
            result=cover_letter,
            llm_model=self.vacancy_ai_assistant.llm_client.model,
        )
        logger.info("✅ Шаблон письма сгенерирован. ID вакансии: %s.", vacancy_id)
        return cover_letter

    async def gen_resume_tips_by_vacancy(self, vacancy_id: str, user_id: str | None = None) -> str:
        """Генерирует рекомендации по составлению резюме под конкретную вакансию.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя для поиска вакансии в избранном.

        Returns:
            HTML-строка с рекомендациями по резюме.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена.
            VacanciesServiceError: При ошибке валидации данных.
        """
        logger.info("🤖 Генерация рекомендаций по резюме. ID вакансии: %s.", vacancy_id)
        vacancy = await self._get_vacancy_by_id_from_favorites(vacancy_id=vacancy_id, user_id=user_id)
        vacancy_dict = vacancy.model_dump()
        resume_tips = await self.vacancy_ai_assistant.gen_resume_tips_by_vacancy(
            vacancy=vacancy_dict
        )
        await self.assistant_session_repository.save_session(
            session_type="resume_tips_by_vacancy",
            vacancy_id=vacancy_id,
            vacancy_name=vacancy_dict.get("vacancy_name", ""),
            employer_name=vacancy_dict.get("employer_name"),
            employer_location=vacancy_dict.get("employer_location"),
            employment=vacancy_dict.get("employment"),
            salary=vacancy_dict.get("salary"),
            description=vacancy_dict.get("description"),
            result=resume_tips,
            llm_model=self.vacancy_ai_assistant.llm_client.model,
        )
        logger.info("✅ Рекомендации по резюме сгенерированы. ID вакансии: %s.", vacancy_id)
        return resume_tips

    async def gen_letter_questionnaire(self, vacancy_id: str, user_id: str | None = None) -> QuestionnaireResponseSchema:
        """Генерирует анкету для составления персонализированного сопроводительного письма.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя для поиска вакансии в избранном.

        Returns:
            Объект QuestionnaireResponseSchema с вопросами анкеты.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена.
            VacanciesServiceError: При ошибке валидации данных.
        """
        logger.info("🤖 Генерация анкеты (письмо). ID вакансии: %s.", vacancy_id)
        vacancy = await self._get_vacancy_by_id_from_favorites(vacancy_id=vacancy_id, user_id=user_id)
        vacancy_dict = vacancy.model_dump()
        questionnaire = await self.vacancy_ai_assistant.gen_letter_questionnaire(
            vacancy=vacancy_dict,
            schema=QuestionnaireResponseSchema,
        )
        await self.assistant_session_repository.save_session(
            session_type="letter_questionnaire",
            vacancy_id=vacancy_id,
            vacancy_name=vacancy_dict.get("vacancy_name", ""),
            employer_name=vacancy_dict.get("employer_name"),
            employer_location=vacancy_dict.get("employer_location"),
            employment=vacancy_dict.get("employment"),
            salary=vacancy_dict.get("salary"),
            description=vacancy_dict.get("description"),
            result=questionnaire.model_dump_json(),
            llm_model=self.vacancy_ai_assistant.llm_client.model,
        )
        logger.info("✅ Анкета (письмо) сгенерирована. ID вакансии: %s.", vacancy_id)
        return questionnaire

    async def gen_resume_questionnaire(self, vacancy_id: str, user_id: str | None = None) -> QuestionnaireResponseSchema:
        """Генерирует анкету для составления персонализированных рекомендаций по резюме.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя для поиска вакансии в избранном.

        Returns:
            Объект QuestionnaireResponseSchema с вопросами анкеты.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена.
            VacanciesServiceError: При ошибке валидации данных.
        """
        logger.info("🤖 Генерация анкеты (резюме). ID вакансии: %s.", vacancy_id)
        vacancy = await self._get_vacancy_by_id_from_favorites(vacancy_id=vacancy_id, user_id=user_id)
        vacancy_dict = vacancy.model_dump()
        questionnaire = await self.vacancy_ai_assistant.gen_resume_questionnaire(
            vacancy=vacancy_dict,
            schema=QuestionnaireResponseSchema,
        )
        await self.assistant_session_repository.save_session(
            session_type="resume_questionnaire",
            vacancy_id=vacancy_id,
            vacancy_name=vacancy_dict.get("vacancy_name", ""),
            employer_name=vacancy_dict.get("employer_name"),
            employer_location=vacancy_dict.get("employer_location"),
            employment=vacancy_dict.get("employment"),
            salary=vacancy_dict.get("salary"),
            description=vacancy_dict.get("description"),
            result=questionnaire.model_dump_json(),
            llm_model=self.vacancy_ai_assistant.llm_client.model,
        )
        logger.info("✅ Анкета (резюме) сгенерирована. ID вакансии: %s.", vacancy_id)
        return questionnaire

    async def gen_cover_letter_by_questionnaire(
        self, vacancy_id: str, answers: list[dict], user_id: str | None = None
    ) -> str:
        """Генерирует персонализированное сопроводительное письмо на основе анкеты.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            answers: Список ответов соискателя на вопросы анкеты.

        Returns:
            HTML-строка с персонализированным сопроводительным письмом.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена.
            VacanciesServiceError: При ошибке валидации данных.
        """
        logger.info(
            "🤖 Генерация персонализированного письма. ID вакансии: %s, ответов: %d.",
            vacancy_id, len(answers),
        )
        vacancy = await self._get_vacancy_by_id_from_favorites(vacancy_id=vacancy_id, user_id=user_id)
        vacancy_dict = vacancy.model_dump()
        cover_letter = await self.vacancy_ai_assistant.gen_cover_letter_by_questionnaire(
            vacancy=vacancy_dict,
            questionnaire=answers,
        )
        await self.assistant_session_repository.save_session(
            session_type="cover_letter_by_questionnaire",
            vacancy_id=vacancy_id,
            vacancy_name=vacancy_dict.get("vacancy_name", ""),
            employer_name=vacancy_dict.get("employer_name"),
            employer_location=vacancy_dict.get("employer_location"),
            employment=vacancy_dict.get("employment"),
            salary=vacancy_dict.get("salary"),
            description=vacancy_dict.get("description"),
            answers=answers,
            result=cover_letter,
            llm_model=self.vacancy_ai_assistant.llm_client.model,
        )
        logger.info("✅ Персонализированное письмо сгенерировано. ID вакансии: %s.", vacancy_id)
        return cover_letter

    async def gen_resume_tips_by_questionnaire(
        self, vacancy_id: str, answers: list[dict], user_id: str | None = None
    ) -> str:
        """Генерирует персонализированные рекомендации по резюме на основе анкеты.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            answers: Список ответов соискателя на вопросы анкеты.

        Returns:
            HTML-строка с персонализированными рекомендациями по резюме.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена.
            VacanciesServiceError: При ошибке валидации данных.
        """
        logger.info(
            "🤖 Генерация персонализированных рекомендаций по резюме. ID вакансии: %s, ответов: %d.",
            vacancy_id, len(answers),
        )
        vacancy = await self._get_vacancy_by_id_from_favorites(vacancy_id=vacancy_id, user_id=user_id)
        vacancy_dict = vacancy.model_dump()
        resume_tips = await self.vacancy_ai_assistant.gen_resume_tips_by_questionnaire(
            vacancy=vacancy_dict,
            questionnaire=answers,
        )
        await self.assistant_session_repository.save_session(
            session_type="resume_tips_by_questionnaire",
            vacancy_id=vacancy_id,
            vacancy_name=vacancy_dict.get("vacancy_name", ""),
            employer_name=vacancy_dict.get("employer_name"),
            employer_location=vacancy_dict.get("employer_location"),
            employment=vacancy_dict.get("employment"),
            salary=vacancy_dict.get("salary"),
            description=vacancy_dict.get("description"),
            answers=answers,
            result=resume_tips,
            llm_model=self.vacancy_ai_assistant.llm_client.model,
        )
        logger.info(
            "✅ Персонализированные рекомендации по резюме сгенерированы. ID вакансии: %s.", vacancy_id
        )
        return resume_tips

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
                    f"Название населённого пункта содержит слишком много частей: {len(split_location)}, "
                    f"максимум: {self.MAX_COUNT_PARTS_IN_LOCATION}."
                )
            )
        
        if not all(
            symbol.isspace() or symbol.isalpha()
            for symbol in (part_name for part_name in split_location)
        ):
            raise LocationValidationError(
                location=location,
                error_details="Название населённого пункта не должно содержать цифры."
            )
        
        if not re.search(r"^[А-Яа-яЁё\s\-]+\Z", location):
            raise LocationValidationError(
                location=location,
                error_details="Название населённого пункта должно содержать только русские буквы."
            )
    
    def _location_name_verification(self, location: str) -> str:
        """Выполняет полную валидацию и нормализацию наименования населенного пункта."""
        hyphen, split_location = self._is_hyphen_exist(location=location)
        self._validate_location(location=location, split_location=split_location)
        return self._normalize_location(
            parts=split_location, hyphen=hyphen
        )

    @staticmethod
    def _deduplicate_vacancies(vacancies: list[dict]) -> list[dict]:
        """Удаляет дубликаты вакансий по паре (vacancy_id, location)."""
        seen = set()
        unique = []
        for v in vacancies:
            key = (v.get("vacancy_id"), v.get("location"))
            if key not in seen:
                seen.add(key)
                unique.append(v)
        duplicates_count = len(vacancies) - len(unique)
        if duplicates_count > 0:
            logger.warning(
                "⚠️ Обнаружены дубликаты вакансий: %d шт. Удалены перед сохранением.",
                duplicates_count,
            )
        return unique

    # Блок приватных методов для получения вакансий в заданном регионе и локации
    async def _get_vacancies_data_from_apis(self, location: str, region_data: dict) -> dict:
        """Агрегирует данные о вакансиях из всех внешних API, выполняя запросы асинхронно."""
        region_code_hh = region_data.get("code_hh")
        region_code_tv = region_data.get("code_tv")

        logger.info(
            "⚡ Асинхронный сбор вакансий из внешних API. Населённый пункт: '%s', коды региона: hh=%s, tv=%s",
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
                "❌ Ошибка при получении данных от hh.ru: %s",
                hh_result, exc_info=hh_result
            )
            error_request_hh = True
            error_details_hh = getattr(hh_result, 'detail', str(hh_result))
        elif isinstance(hh_result, Exception):
            logger.error(
                "❌ Непредвиденная ошибка при получении данных от hh.ru: %s",
                hh_result, exc_info=hh_result
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
                "❌ Ошибка при получении данных от trudvsem.ru: %s",
                tv_result, exc_info=tv_result
            )
            error_request_tv = True
            error_details_tv = getattr(tv_result, 'detail', str(tv_result))
        elif isinstance(tv_result, Exception):
            logger.error(
                "❌ Непредвиденная ошибка при получении данных от trudvsem.ru: %s",
                tv_result, exc_info=tv_result
            )
            error_request_tv = True
            error_details_tv = str(tv_result)
        else:
            vacancies.extend(tv_result.get('vacancies', []))
            vacancies_count_tv = tv_result.get('vacancies_count', 0)

        all_vacancies_count = vacancies_count_hh + vacancies_count_tv
        vacancies = self._deduplicate_vacancies(vacancies)

        counts_by_source: dict[str, int] = {}
        for v in vacancies:
            source = v.get("vacancy_source", "")
            counts_by_source[source] = counts_by_source.get(source, 0) + 1

        vacancies_count_hh = counts_by_source.get("hh.ru", 0)
        vacancies_count_tv = counts_by_source.get("trudvsem.ru", 0)

        logger.info(
            "✅ Сбор вакансий завершён. hh.ru: %d, trudvsem.ru: %d. Итого: %s (уникальных: %d)",
            vacancies_count_hh, vacancies_count_tv, all_vacancies_count, len(vacancies)
        )

        return {
            "vacancies": vacancies,
            "error_request_hh": error_request_hh,
            "error_request_tv": error_request_tv,
            "error_details_hh": error_details_hh,
            "error_details_tv": error_details_tv,
            "all_vacancies_count": len(vacancies),
            "vacancies_count_hh": vacancies_count_hh,
            "vacancies_count_tv": vacancies_count_tv,
        }

    async def _get_vacancies_tv_api(self, location: str, region_code_tv: str) -> dict:
        """Получает и парсит вакансии с сайта 'Работа России'."""
        vacancies_raw = await self.tv_client_api.get_vacancies_in_region(
            region_code_tv=region_code_tv
        )

        if not vacancies_raw:
            raise VacanciesNotFoundError(
                source="trudvsem.ru API",
                region_code=region_code_tv,
                location=location
            )

        loop = asyncio.get_event_loop()
        vacancies = await loop.run_in_executor(
            None,
            functools.partial(self.vacancies_parser.parse_vacancies_tv, vacancies=vacancies_raw, location=location),
        )

        return {"vacancies": vacancies, "vacancies_count": len(vacancies)}

    async def _get_vacancies_hh_api(self, location: str, region_code_hh: str) -> dict:
        """Получает и парсит вакансии с сайта 'hh.ru'."""
        vacancies_raw = await self.hh_client_api.get_vacancies_in_location(
            location=location,
            region_code_hh=region_code_hh
        )

        if not vacancies_raw:
            raise VacanciesNotFoundError(
                source="HH.ru API",
                region_code=region_code_hh,
                location=location
            )

        loop = asyncio.get_event_loop()
        vacancies = await loop.run_in_executor(
            None,
            functools.partial(self.vacancies_parser.parse_vacancies_hh, vacancies=vacancies_raw, location=location),
        )

        return {"vacancies": vacancies, "vacancies_count": len(vacancies_raw)}

    async def _save_vacancies_data(
        self,
        all_vacancies_count: int,
        location: str,
        vacancies: list[dict]
    ) -> None:
        """Сохраняет данные о вакансиях в БД, предварительно удаляя старые."""
        logger.info("💾 Обновление вакансий в БД. Населённый пункт: '%s'.", location)

        await self.vacancies_repository.delete_vacancies_by_location(
            location=location
        )

        if all_vacancies_count > 0:
            await self.vacancies_repository.save_vacancies(
                vacancies=vacancies
            )
            logger.info(
                "✅ Вакансии сохранены в БД: %d записей. Населённый пункт: '%s'.",
                all_vacancies_count, location
            )
        else:
            logger.info(
                "💾 Вакансии в БД обновлены: новых записей нет, старые удалены. Населённый пункт: '%s'.",
                location
            )

    # Блок приватных методов для запроса информации по отдельной вакансии
    async def _get_vacancy_by_id_from_favorites(
            self,
            vacancy_id: str,
            user_id: str | None = None
    ) -> VacancySchema:
        """
        Возвращает детальную информацию по вакансии из избранного с TTL-логикой.

        Если данные свежие (< FAVORITES_TTL_HOURS) — возвращает snapshot из БД.
        Если устарели — обновляет через внешний API и сохраняет в БД.
        При ошибке API возвращает snapshot.

        Args:
            vacancy_id: Уникальный идентификатор вакансии.
            user_id: Идентификатор пользователя. Если указан — ищет вакансию только
                     среди избранного этого пользователя. Если None — среди всех записей.

        Returns:
            Объект `VacancySchema` с детальной информацией о вакансии.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена в избранном.
            VacanciesServiceError: При ошибке валидации или неизвестном источнике.
        """
        logger.info("🔍 Поиск вакансии в избранном. ID: %s", vacancy_id)

        vacancy_raw = await self.favorites_repository.get_vacancy_by_id(
            vacancy_id=vacancy_id, user_id=user_id
        )
        if not vacancy_raw:
            logger.warning("⚠️ Вакансия не найдена в таблице избранного. ID: %s", vacancy_id)
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Вакансия с указанным ID не найдена в избранном."
            )

        ttl_threshold = datetime.now(timezone.utc) - timedelta(hours=self.FAVORITES_TTL_HOURS)
        updated_at = vacancy_raw.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        if updated_at >= ttl_threshold:
            logger.info("✅ Вакансия в избранном свежая (<24h). ID: %s. Возвращаем из БД.", vacancy_id)
            result = VacancySchema.model_validate(vacancy_raw)
            result.is_favorite = True
            return result

        logger.info(
            "🔄 Вакансия в избранном устарела (>24h). ID: %s, источник: %s. Запрашиваем из источника.",
            vacancy_id, vacancy_raw.vacancy_source
        )
        try:
            vacancy_data = await self._fetch_vacancy_details_from_api(
                vacancy_id=vacancy_raw.vacancy_id,
                vacancy_source=vacancy_raw.vacancy_source,
                employer_code=vacancy_raw.employer_code,
            )

            update_data = {k: v for k, v in vacancy_data.items() if k != "is_favorite"}
            await self.favorites_repository.update_vacancy(
                vacancy_id=vacancy_raw.vacancy_id,
                user_id=vacancy_raw.user_id,
                data=update_data,
            )
            try:
                result = VacancySchema.model_validate(vacancy_data)
                result.is_favorite = True
                return result
            except ValidationError as error:
                raise VacanciesServiceError(
                    error_details="Ошибка валидации данных при получении информации о вакансии из избранного."
                ) from error

        except VacancyNotFoundError:
            logger.warning(
                "⚠️ Вакансия не найдена во внешнем источнике. ID: %s. Обновляем статус.",
                vacancy_id
            )
            await self.favorites_repository.update_vacancy(
                vacancy_id=vacancy_raw.vacancy_id,
                user_id=vacancy_raw.user_id,
                data={"status": self.FLAG_VACANCY_NOT_FOUND},
            )
            result = VacancySchema.model_validate(vacancy_raw)
            result.status = self.FLAG_VACANCY_NOT_FOUND
            result.is_favorite = True
            return result

        except (HHAPIRequestError, TVAPIRequestError) as error:
            logger.error(
                "❌ Ошибка API при получении вакансии из избранного. ID: %s: %s",
                vacancy_id, error
            )
            result = VacancySchema.model_validate(vacancy_raw)
            result.is_favorite = True
            return result

    async def _fetch_vacancy_details_from_api(
        self,
        vacancy_id: str,
        vacancy_source: str,
        employer_code: str,
    ) -> dict:
        """
        Запрашивает детальную информацию о вакансии из внешнего API по источнику.

        Args:
            vacancy_id: Идентификатор вакансии.
            vacancy_source: Источник ('hh.ru' или 'trudvsem.ru').
            employer_code: Код работодателя (нужен для trudvsem.ru).

        Returns:
            Словарь с детальными данными вакансии.

        Raises:
            VacancyNotFoundError: Если вакансия не найдена во внешнем источнике.
            HHAPIRequestError: При ошибке запроса к hh.ru.
            TVAPIRequestError: При ошибке запроса к trudvsem.ru.
            VacanciesServiceError: Если источник вакансии неизвестен.
        """
        if vacancy_source == "hh.ru":
            logger.info("🔍 Запрашиваем детальную информацию из hh.ru. ID: %s", vacancy_id)
            return await self._get_vacancy_details_hh_api(vacancy_id=vacancy_id)
        elif vacancy_source == "trudvsem.ru":
            logger.info("🔍 Запрашиваем детальную информацию из trudvsem.ru. ID: %s", vacancy_id)
            return await self._get_vacancy_details_tv_api(
                vacancy_id=vacancy_id,
                employer_code=employer_code,
            )
        else:
            logger.warning(
                "⚠️ Неизвестный источник вакансии: '%s'. ID вакансии: %s.",
                vacancy_source, vacancy_id
            )
            raise VacanciesServiceError(
                error_details=f"Неизвестный источник вакансии: '{vacancy_source}'."
            )

    async def _get_vacancy_details_hh_api(self, vacancy_id: str):
        """Получает и парсит детальную информацию о вакансии от hh.ru API."""
        vacancy_request_result = await self.hh_client_api.get_one_vacancy(
            vacancy_id=vacancy_id
        )
        search_status = vacancy_request_result.get("search_status")
        if search_status == self.FLAG_VACANCY_NOT_FOUND:
            logger.warning("⚠️ Вакансия не найдена в hh.ru. ID: %s", vacancy_id)
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Вакансия не найдена во внешнем источнике (hh.ru)."
            )

        vacancy_raw = vacancy_request_result.get("response_data")

        return self.vacancies_parser.parse_vacancy_details_hh(vacancy=vacancy_raw)

    async def _get_vacancy_details_tv_api(self, vacancy_id: str, employer_code: str):
        """Получает и парсит детальную информацию о вакансии от trudvsem.ru API."""
        vacancy_raw = await self.tv_client_api.get_one_vacancy(
            vacancy_id=vacancy_id,
            employer_code=employer_code
        )
        if not vacancy_raw:
            logger.warning("⚠️ Вакансия не найдена в trudvsem.ru. ID: %s", vacancy_id)
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Вакансия не найдена во внешнем источнике (trudvsem.ru)."
            )
        
        return self.vacancies_parser.parse_vacancy_details_tv(
            vacancy=vacancy_raw
        )

    async def _get_vacancy_by_id(self, vacancy_id: str) -> Vacancies:
        """Возвращает данные вакансии из БД по ее ID."""
        vacancy_raw = await self.vacancies_repository.get_vacancy_by_id(
            vacancy_id=vacancy_id
        )
        if not vacancy_raw:
            logger.warning("⚠️ Вакансия не найдена в БД. ID: %s", vacancy_id)
            raise VacancyNotFoundError(
                vacancy_id=vacancy_id,
                error_details="Вакансия с указанным ID не найдена."
            )

        try:
            vacancy = VacancySchema.model_validate(vacancy_raw)
            return vacancy
        except ValidationError as error:
            raise VacanciesServiceError(
                error_details="Ошибка валидации данных вакансии."
            ) from error

    async def _fetch_one_favorite_vacancy(self, vacancy: FavoriteVacancies) -> dict:
        """
        Асинхронно получает детальную информацию по одной вакансии с TTL-логикой.

        Если данные свежие (< FAVORITES_TTL_HOURS) — возвращает snapshot из БД.
        Если устарели — обновляет через внешний API и сохраняет в БД.
        При ошибке API возвращает snapshot, не ломая список.
        """
        async with self.semaphore:
            ttl_threshold = datetime.now(timezone.utc) - timedelta(hours=self.FAVORITES_TTL_HOURS)
            updated_at = vacancy.updated_at
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)

            if updated_at >= ttl_threshold:
                logger.info(
                    "✅ Избранная вакансия свежая (<24h). ID: %s. Возвращаем из БД.",
                    vacancy.vacancy_id
                )
                result = VacancySchema.model_validate(vacancy).model_dump()
                result["is_favorite"] = True
                return result

            logger.info(
                "🔄 Избранная вакансия устарела (>24h). ID: %s. Запрашиваем из источника.",
                vacancy.vacancy_id
            )
            try:
                vacancy_data = await self._fetch_vacancy_details_from_api(
                    vacancy_id=vacancy.vacancy_id,
                    vacancy_source=vacancy.vacancy_source,
                    employer_code=vacancy.employer_code,
                )

                update_data = {k: v for k, v in vacancy_data.items() if k != "is_favorite"}
                await self.favorites_repository.update_vacancy(
                    vacancy_id=vacancy.vacancy_id,
                    user_id=vacancy.user_id,
                    data=update_data,
                )
                vacancy_data["is_favorite"] = True
                return vacancy_data

            except VacancyNotFoundError:
                logger.warning(
                    "⚠️ Вакансия не найдена во внешнем источнике. ID: %s. Обновляем статус.",
                    vacancy.vacancy_id
                )
                await self.favorites_repository.update_vacancy(
                    vacancy_id=vacancy.vacancy_id,
                    user_id=vacancy.user_id,
                    data={"status": self.FLAG_VACANCY_NOT_FOUND},
                )
                vacancy_dict = VacancySchema.model_validate(vacancy).model_dump()
                vacancy_dict["status"] = self.FLAG_VACANCY_NOT_FOUND
                vacancy_dict["is_favorite"] = True
                return vacancy_dict

            except (HHAPIRequestError, TVAPIRequestError) as error:
                logger.error(
                    "❌ Ошибка API при обновлении избранной вакансии %s: %s",
                    vacancy.vacancy_id, error
                )
                result = VacancySchema.model_validate(vacancy).model_dump()
                result["is_favorite"] = True
                return result

    async def _compile_enriched_favorite_vacancies(
        self, vacancies_raw: list[FavoriteVacancies]
    ) -> list:
        """
        Обогащает список избранных вакансий актуальными данными из внешних API,
        используя семафор для ограничения одновременных запросов.
        """
        logger.info("⚡ Обогащение данных избранных вакансий из внешних API.")

        tasks = [self._fetch_one_favorite_vacancy(vacancy) for vacancy in vacancies_raw]
        compiled_vacancies = await asyncio.gather(*tasks)

        return compiled_vacancies
