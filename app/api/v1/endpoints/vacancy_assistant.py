import logging

from fastapi import APIRouter, HTTPException, Path, Query, status

from dependencies.services import VacanciesServiceDep
from exceptions.repositories import VacanciesRepositoryError
from exceptions.services import VacanciesServiceError
from exceptions.vacancies import VacancyNotFoundError
from schemas.vacancy_assistant import (
    AssistantQuestionnaireRequestSchema,
    AssistantTextResponseSchema,
    QuestionnaireResponseSchema,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    path="/cover-letter/questionnaire/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Анкета для сопроводительного письма",
    description=(
        "Генерирует персонализированную анкету (5–7 вопросов) на основе данных вакансии. "
        "Ответы на анкету передаются в POST /cover-letter/by-questionnaire/{vacancy_id} "
        "для получения персонализированного письма."
    ),
    responses={
        200: {"description": "Анкета успешно сгенерирована."},
        401: {"description": "API-ключ отсутствует или невалиден."},
        403: {"description": "API-ключ просрочен или деактивирован."},
        404: {"description": "Вакансия с указанным ID не найдена."},
        500: {"description": "Внутренняя ошибка сервера или ошибка обращения к LLM."},
    },
    response_model=QuestionnaireResponseSchema,
)
async def gen_letter_questionnaire(
    service: VacanciesServiceDep,
    vacancy_id: str = Path(description="Уникальный идентификатор вакансии."),
    user_id: str | None = Query(None, description="Идентификатор пользователя."),
) -> QuestionnaireResponseSchema:
    """Генерирует анкету для составления персонализированного сопроводительного письма.

    Args:
        service: Зависимость, предоставляющая доступ к бизнес-логике.
        vacancy_id: Уникальный идентификатор вакансии.
        user_id: Идентификатор пользователя.

    Returns:
        Объект QuestionnaireResponseSchema с вопросами анкеты.

    Raises:
        HTTPException: 404, если вакансия не найдена; 500 при внутренней ошибке.
    """
    logger.info("Запрос GET /cover-letter/questionnaire/%s.", vacancy_id)
    try:
        result = await service.gen_letter_questionnaire(vacancy_id=vacancy_id, user_id=user_id)
        logger.info("Успешная генерация анкеты (письмо). ID вакансии: %s.", vacancy_id)
        return result
    except (VacancyNotFoundError, VacanciesServiceError, VacanciesRepositoryError) as error:
        logger.error(
            "Ошибка при генерации анкеты (письмо). ID вакансии: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/resume-tips/questionnaire/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Анкета для рекомендаций по резюме",
    description=(
        "Генерирует персонализированную анкету (5–7 вопросов) на основе данных вакансии. "
        "Ответы на анкету передаются в POST /resume-tips/by-questionnaire/{vacancy_id} "
        "для получения персонализированных рекомендаций."
    ),
    responses={
        200: {"description": "Анкета успешно сгенерирована."},
        401: {"description": "API-ключ отсутствует или невалиден."},
        403: {"description": "API-ключ просрочен или деактивирован."},
        404: {"description": "Вакансия с указанным ID не найдена."},
        500: {"description": "Внутренняя ошибка сервера или ошибка обращения к LLM."},
    },
    response_model=QuestionnaireResponseSchema,
)
async def gen_resume_questionnaire(
    service: VacanciesServiceDep,
    vacancy_id: str = Path(description="Уникальный идентификатор вакансии."),
    user_id: str | None = Query(None, description="Идентификатор пользователя."),
) -> QuestionnaireResponseSchema:
    """Генерирует анкету для составления персонализированных рекомендаций по резюме.

    Args:
        service: Зависимость, предоставляющая доступ к бизнес-логике.
        vacancy_id: Уникальный идентификатор вакансии.
        user_id: Идентификатор пользователя.

    Returns:
        Объект QuestionnaireResponseSchema с вопросами анкеты.

    Raises:
        HTTPException: 404, если вакансия не найдена; 500 при внутренней ошибке.
    """
    logger.info("Запрос GET /resume-tips/questionnaire/%s.", vacancy_id)
    try:
        result = await service.gen_resume_questionnaire(vacancy_id=vacancy_id, user_id=user_id)
        logger.info("Успешная генерация анкеты (резюме). ID вакансии: %s.", vacancy_id)
        return result
    except (VacancyNotFoundError, VacanciesServiceError, VacanciesRepositoryError) as error:
        logger.error(
            "Ошибка при генерации анкеты (резюме). ID вакансии: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/cover-letter/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Шаблон сопроводительного письма",
    description=(
        "Генерирует шаблон сопроводительного письма и краткий совет на основе данных вакансии. "
        "Для получения персонализированного письма сначала получите анкету через "
        "GET /cover-letter/questionnaire/{vacancy_id}, заполните её и передайте в "
        "POST /cover-letter/by-questionnaire/{vacancy_id}."
    ),
    responses={
        200: {"description": "Шаблон письма успешно сгенерирован."},
        401: {"description": "API-ключ отсутствует или невалиден."},
        403: {"description": "API-ключ просрочен или деактивирован."},
        404: {"description": "Вакансия с указанным ID не найдена."},
        500: {"description": "Внутренняя ошибка сервера или ошибка обращения к LLM."},
    },
    response_model=AssistantTextResponseSchema,
)
async def gen_cover_letter_by_vacancy(
    service: VacanciesServiceDep,
    vacancy_id: str = Path(description="Уникальный идентификатор вакансии."),
    user_id: str | None = Query(None, description="Идентификатор пользователя."),
) -> AssistantTextResponseSchema:
    """Генерирует шаблон сопроводительного письма на основе данных вакансии.

    Args:
        service: Зависимость, предоставляющая доступ к бизнес-логике.
        vacancy_id: Уникальный идентификатор вакансии.
        user_id: Идентификатор пользователя.

    Returns:
        Объект AssistantTextResponseSchema с HTML-текстом шаблона и совета.

    Raises:
        HTTPException: 404, если вакансия не найдена; 500 при внутренней ошибке.
    """
    logger.info("Запрос GET /cover-letter/%s.", vacancy_id)
    try:
        result = await service.gen_cover_letter_by_vacancy(vacancy_id=vacancy_id, user_id=user_id)
        logger.info("Успешная генерация шаблона письма. ID вакансии: %s.", vacancy_id)
        return AssistantTextResponseSchema(result=result)
    except (VacancyNotFoundError, VacanciesServiceError, VacanciesRepositoryError) as error:
        logger.error(
            "Ошибка при генерации шаблона письма. ID вакансии: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/resume-tips/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Рекомендации по резюме",
    description=(
        "Генерирует рекомендации по составлению резюме под конкретную вакансию. "
        "Для получения персонализированных рекомендаций сначала получите анкету через "
        "GET /resume-tips/questionnaire/{vacancy_id}, заполните её и передайте в "
        "POST /resume-tips/by-questionnaire/{vacancy_id}."
    ),
    responses={
        200: {"description": "Рекомендации по резюме успешно сгенерированы."},
        401: {"description": "API-ключ отсутствует или невалиден."},
        403: {"description": "API-ключ просрочен или деактивирован."},
        404: {"description": "Вакансия с указанным ID не найдена."},
        500: {"description": "Внутренняя ошибка сервера или ошибка обращения к LLM."},
    },
    response_model=AssistantTextResponseSchema,
)
async def gen_resume_tips_by_vacancy(
    service: VacanciesServiceDep,
    vacancy_id: str = Path(description="Уникальный идентификатор вакансии."),
    user_id: str | None = Query(None, description="Идентификатор пользователя."),
) -> AssistantTextResponseSchema:
    """Генерирует рекомендации по составлению резюме на основе данных вакансии.

    Args:
        service: Зависимость, предоставляющая доступ к бизнес-логике.
        vacancy_id: Уникальный идентификатор вакансии.
        user_id: Идентификатор пользователя.

    Returns:
        Объект AssistantTextResponseSchema с HTML-текстом рекомендаций.

    Raises:
        HTTPException: 404, если вакансия не найдена; 500 при внутренней ошибке.
    """
    logger.info("Запрос GET /resume-tips/%s.", vacancy_id)
    try:
        result = await service.gen_resume_tips_by_vacancy(vacancy_id=vacancy_id, user_id=user_id)
        logger.info("Успешная генерация рекомендаций по резюме. ID вакансии: %s.", vacancy_id)
        return AssistantTextResponseSchema(result=result)
    except (VacancyNotFoundError, VacanciesServiceError, VacanciesRepositoryError) as error:
        logger.error(
            "Ошибка при генерации рекомендаций по резюме. ID вакансии: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/cover-letter/by-questionnaire/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Персонализированное сопроводительное письмо",
    description=(
        "Генерирует персонализированное сопроводительное письмо на основе ответов "
        "соискателя на анкету и данных вакансии. "
        "Анкету предварительно нужно получить через GET /cover-letter/questionnaire/{vacancy_id}."
    ),
    responses={
        200: {"description": "Персонализированное письмо успешно сгенерировано."},
        401: {"description": "API-ключ отсутствует или невалиден."},
        403: {"description": "API-ключ просрочен или деактивирован."},
        404: {"description": "Вакансия с указанным ID не найдена."},
        500: {"description": "Внутренняя ошибка сервера или ошибка обращения к LLM."},
    },
    response_model=AssistantTextResponseSchema,
)
async def gen_cover_letter_by_questionnaire(
    data: AssistantQuestionnaireRequestSchema,
    service: VacanciesServiceDep,
    vacancy_id: str = Path(description="Уникальный идентификатор вакансии."),
    user_id: str | None = Query(None, description="Идентификатор пользователя."),
) -> AssistantTextResponseSchema:
    """Генерирует персонализированное сопроводительное письмо на основе анкеты.

    Args:
        data: Список ответов соискателя на вопросы анкеты.
        service: Зависимость, предоставляющая доступ к бизнес-логике.
        vacancy_id: Уникальный идентификатор вакансии.
        user_id: Идентификатор пользователя.

    Returns:
        Объект AssistantTextResponseSchema с HTML-текстом готового письма.

    Raises:
        HTTPException: 404, если вакансия не найдена; 500 при внутренней ошибке.
    """
    logger.info(
        "Запрос POST /cover-letter/by-questionnaire/%s. Количество ответов: %d.",
        vacancy_id,
        len(data.answers),
    )
    try:
        answers = [answer.model_dump() for answer in data.answers]
        result = await service.gen_cover_letter_by_questionnaire(
            vacancy_id=vacancy_id, answers=answers, user_id=user_id
        )
        logger.info(
            "Успешная генерация персонализированного письма. ID вакансии: %s.", vacancy_id
        )
        return AssistantTextResponseSchema(result=result)
    except (VacancyNotFoundError, VacanciesServiceError, VacanciesRepositoryError) as error:
        logger.error(
            "Ошибка при генерации персонализированного письма. ID вакансии: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post(
    path="/resume-tips/by-questionnaire/{vacancy_id}",
    status_code=status.HTTP_200_OK,
    summary="Персонализированные рекомендации по резюме",
    description=(
        "Генерирует персонализированные рекомендации по составлению резюме на основе "
        "ответов соискателя на анкету и данных вакансии. "
        "Анкету предварительно нужно получить через GET /resume-tips/questionnaire/{vacancy_id}."
    ),
    responses={
        200: {"description": "Персонализированные рекомендации успешно сгенерированы."},
        401: {"description": "API-ключ отсутствует или невалиден."},
        403: {"description": "API-ключ просрочен или деактивирован."},
        404: {"description": "Вакансия с указанным ID не найдена."},
        500: {"description": "Внутренняя ошибка сервера или ошибка обращения к LLM."},
    },
    response_model=AssistantTextResponseSchema,
)
async def gen_resume_tips_by_questionnaire(
    data: AssistantQuestionnaireRequestSchema,
    service: VacanciesServiceDep,
    vacancy_id: str = Path(description="Уникальный идентификатор вакансии."),
    user_id: str | None = Query(None, description="Идентификатор пользователя."),
) -> AssistantTextResponseSchema:
    """Генерирует персонализированные рекомендации по резюме на основе анкеты.

    Args:
        data: Список ответов соискателя на вопросы анкеты.
        service: Зависимость, предоставляющая доступ к бизнес-логике.
        vacancy_id: Уникальный идентификатор вакансии.
        user_id: Идентификатор пользователя.

    Returns:
        Объект AssistantTextResponseSchema с HTML-текстом персонализированных рекомендаций.

    Raises:
        HTTPException: 404, если вакансия не найдена; 500 при внутренней ошибке.
    """
    logger.info(
        "Запрос POST /resume-tips/by-questionnaire/%s. Количество ответов: %d.",
        vacancy_id,
        len(data.answers),
    )
    try:
        answers = [answer.model_dump() for answer in data.answers]
        result = await service.gen_resume_tips_by_questionnaire(
            vacancy_id=vacancy_id, answers=answers, user_id=user_id
        )
        logger.info(
            "Успешная генерация персонализированных рекомендаций. ID вакансии: %s.", vacancy_id
        )
        return AssistantTextResponseSchema(result=result)
    except (VacancyNotFoundError, VacanciesServiceError, VacanciesRepositoryError) as error:
        logger.error(
            "Ошибка при генерации персонализированных рекомендаций. ID вакансии: %s. Детали: %s",
            vacancy_id,
            error,
        )
        raise HTTPException(status_code=error.status_code, detail=error.detail)
