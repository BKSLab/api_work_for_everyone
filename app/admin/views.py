import json

from markupsafe import Markup
from sqladmin import ModelView

from db.models.api_keys import ApiKey
from db.models.assistant_session import AssistantSession
from db.models.favorites import FavoriteVacancies
from db.models.search_event import SearchEvent

_QUESTIONNAIRE_TYPES = {
    "letter_questionnaire",
    "resume_questionnaire",
}

_SESSION_TYPE_COLORS = {
    "cover_letter_by_vacancy": "#F5B800",
    "resume_tips_by_vacancy": "#F5B800",
    "letter_questionnaire": "#3B82F6",
    "resume_questionnaire": "#3B82F6",
    "cover_letter_by_questionnaire": "#22C55E",
    "resume_tips_by_questionnaire": "#22C55E",
}

_SESSION_TYPE_LABELS = {
    "cover_letter_by_vacancy": "Письмо по вакансии",
    "resume_tips_by_vacancy": "Советы по резюме (вакансия)",
    "letter_questionnaire": "Анкета для письма",
    "resume_questionnaire": "Анкета для резюме",
    "cover_letter_by_questionnaire": "Письмо по анкете",
    "resume_tips_by_questionnaire": "Советы по резюме (анкета)",
}


def _fmt_session_type(model: AssistantSession, attr: str) -> Markup:
    color = _SESSION_TYPE_COLORS.get(model.session_type, "#888")
    label = _SESSION_TYPE_LABELS.get(model.session_type, model.session_type)
    return Markup(
        f'<span style="background:{color};color:#000;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em;font-weight:600;">'
        f"{label}</span>"
    )


_TEXT_STYLE = "white-space:pre-wrap;word-break:break-word;max-width:800px;display:block;"


def _fmt_answers(model: AssistantSession, attr: str) -> Markup:
    if not model.answers:
        return Markup("<em>—</em>")
    items = "".join(
        f"<li style='margin-bottom:0.5em'>"
        f"<div style='font-weight:600;margin-bottom:2px'>{a.get('text', '?')}</div>"
        f"<div style='padding-left:0.8em'>{a.get('answer', '—')}</div>"
        f"</li>"
        for a in model.answers
    )
    return Markup(f"<ul style='margin:0;padding-left:1.2em;list-style:none'>{items}</ul>")


def _fmt_result(model: AssistantSession, attr: str) -> Markup:
    if model.session_type in _QUESTIONNAIRE_TYPES:
        try:
            parsed = json.loads(model.result)
            pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            pretty = model.result
        return Markup(f"<pre style='{_TEXT_STYLE}'>{pretty}</pre>")
    return Markup(f"<div style='{_TEXT_STYLE}'>{model.result}</div>")


def _fmt_text(model: AssistantSession, attr: str) -> Markup:
    value = getattr(model, attr, None) or ""
    return Markup(f"<div style='{_TEXT_STYLE}'>{value}</div>")


def _fmt_is_active(model: ApiKey, attr: str) -> Markup:
    if model.is_active:
        return Markup(
            '<span style="background:#22C55E;color:#000;padding:2px 8px;'
            'border-radius:4px;font-size:0.8em;font-weight:600;">активен</span>'
        )
    return Markup(
        '<span style="background:#EF4444;color:#fff;padding:2px 8px;'
        'border-radius:4px;font-size:0.8em;font-weight:600;">деактивирован</span>'
    )


def _fmt_vacancy_source(model: FavoriteVacancies, attr: str) -> Markup:
    colors = {"hh.ru": "#EF4444", "trudvsem.ru": "#3B82F6"}
    color = colors.get(model.vacancy_source, "#888")
    return Markup(
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em;font-weight:600;">'
        f"{model.vacancy_source}</span>"
    )


def _fmt_fav_status(model: FavoriteVacancies, attr: str) -> Markup:
    if model.status == "not_found":
        return Markup(
            '<span style="background:#6B7280;color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:0.8em">not_found</span>'
        )
    return Markup(
        f'<span style="background:#22C55E;color:#000;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em">{model.status or "actual"}</span>'
    )


class ApiKeyAdmin(ModelView, model=ApiKey):
    name = "API Key"
    name_plural = "API Keys"
    icon = "fa-solid fa-key"

    column_list = [
        ApiKey.id,
        ApiKey.api_key_prefix,
        ApiKey.issued_for,
        ApiKey.owner_email,
        ApiKey.is_active,
        ApiKey.created_at,
        ApiKey.expires_at,
        ApiKey.comment,
    ]
    column_searchable_list = [
        ApiKey.issued_for,
        ApiKey.owner_email,
        ApiKey.api_key_prefix,
    ]
    column_sortable_list = [ApiKey.created_at, ApiKey.is_active]
    column_default_sort = [(ApiKey.created_at, True)]

    form_columns = [
        ApiKey.issued_for,
        ApiKey.owner_email,
        ApiKey.comment,
        ApiKey.expires_at,
        ApiKey.is_active,
    ]

    column_formatters = {ApiKey.is_active: _fmt_is_active}
    column_formatters_detail = {ApiKey.is_active: _fmt_is_active}

    can_create = False
    can_delete = False


class FavoritesAdmin(ModelView, model=FavoriteVacancies):
    name = "Избранное"
    name_plural = "Избранные вакансии"
    icon = "fa-solid fa-heart"

    column_list = [
        FavoriteVacancies.user_id,
        FavoriteVacancies.vacancy_name,
        FavoriteVacancies.employer_name,
        FavoriteVacancies.vacancy_source,
        FavoriteVacancies.location,
        FavoriteVacancies.salary,
        FavoriteVacancies.status,
        FavoriteVacancies.updated_at,
    ]
    column_searchable_list = [
        FavoriteVacancies.user_id,
        FavoriteVacancies.vacancy_name,
        FavoriteVacancies.employer_name,
    ]
    column_sortable_list = [FavoriteVacancies.updated_at]
    column_default_sort = [(FavoriteVacancies.updated_at, True)]

    column_formatters = {
        FavoriteVacancies.vacancy_source: _fmt_vacancy_source,
        FavoriteVacancies.status: _fmt_fav_status,
    }
    column_formatters_detail = {
        FavoriteVacancies.vacancy_source: _fmt_vacancy_source,
        FavoriteVacancies.status: _fmt_fav_status,
    }

    can_create = False
    can_edit = False
    can_delete = False


class AssistantSessionAdmin(ModelView, model=AssistantSession):
    name = "Сессия ассистента"
    name_plural = "Сессии ассистента"
    icon = "fa-solid fa-robot"

    column_list = [
        AssistantSession.id,
        AssistantSession.session_type,
        AssistantSession.vacancy_name,
        AssistantSession.employer_name,
        AssistantSession.vacancy_id,
        AssistantSession.llm_model,
        AssistantSession.created_at,
    ]
    column_searchable_list = [
        AssistantSession.vacancy_name,
        AssistantSession.employer_name,
        AssistantSession.vacancy_id,
    ]
    column_sortable_list = [AssistantSession.created_at, AssistantSession.session_type]
    column_default_sort = [(AssistantSession.created_at, True)]

    column_formatters = {AssistantSession.session_type: _fmt_session_type}
    column_formatters_detail = {
        AssistantSession.session_type: _fmt_session_type,
        AssistantSession.answers: _fmt_answers,
        AssistantSession.result: _fmt_result,
        AssistantSession.description: _fmt_text,
        AssistantSession.vacancy_name: _fmt_text,
        AssistantSession.employer_name: _fmt_text,
    }

    can_create = False
    can_edit = False
    can_delete = True


def _fmt_error_flag(value: bool) -> Markup:
    if value:
        return Markup(
            '<span style="background:#EF4444;color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:0.8em;font-weight:600;">ошибка</span>'
        )
    return Markup(
        '<span style="background:#22C55E;color:#000;padding:2px 8px;'
        'border-radius:4px;font-size:0.8em;font-weight:600;">ок</span>'
    )


def _fmt_error_hh(model: SearchEvent, attr: str) -> Markup:
    return _fmt_error_flag(model.error_hh)


def _fmt_error_tv(model: SearchEvent, attr: str) -> Markup:
    return _fmt_error_flag(model.error_tv)


class SearchEventAdmin(ModelView, model=SearchEvent):
    name = "Событие поиска"
    name_plural = "Статистика поиска"
    icon = "fa-solid fa-chart-bar"

    column_list = [
        SearchEvent.id,
        SearchEvent.location,
        SearchEvent.region_name,
        SearchEvent.region_code,
        SearchEvent.count_hh,
        SearchEvent.count_tv,
        SearchEvent.total_count,
        SearchEvent.error_hh,
        SearchEvent.error_tv,
        SearchEvent.created_at,
    ]
    column_searchable_list = [
        SearchEvent.location,
        SearchEvent.region_name,
        SearchEvent.region_code,
    ]
    column_sortable_list = [
        SearchEvent.created_at,
        SearchEvent.total_count,
        SearchEvent.location,
    ]
    column_default_sort = [(SearchEvent.created_at, True)]

    column_formatters = {
        SearchEvent.error_hh: _fmt_error_hh,
        SearchEvent.error_tv: _fmt_error_tv,
    }
    column_formatters_detail = {
        SearchEvent.error_hh: _fmt_error_hh,
        SearchEvent.error_tv: _fmt_error_tv,
    }

    can_create = False
    can_edit = False
    can_delete = False
