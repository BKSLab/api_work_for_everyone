import json
from datetime import datetime, timedelta, timezone

from markupsafe import Markup
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqladmin import BaseView, ModelView, expose
from starlette.requests import Request
from starlette.responses import Response

from db.models.api_keys import ApiKey
from db.models.assistant_session import AssistantSession
from db.models.favorite_event import FavoriteEvent
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


def _fmt_fav_event_action(model: FavoriteEvent, attr: str) -> Markup:
    if model.action == "add":
        return Markup(
            '<span style="background:#22C55E;color:#000;padding:2px 8px;'
            'border-radius:4px;font-size:0.8em;font-weight:600;">добавлено</span>'
        )
    return Markup(
        '<span style="background:#6B7280;color:#fff;padding:2px 8px;'
        'border-radius:4px;font-size:0.8em;font-weight:600;">удалено</span>'
    )


def _fmt_fav_event_source(model: FavoriteEvent, attr: str) -> Markup:
    colors = {"hh.ru": "#EF4444", "trudvsem.ru": "#3B82F6"}
    color = colors.get(model.vacancy_source or "", "#888")
    return Markup(
        f'<span style="background:{color};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.8em;font-weight:600;">'
        f"{model.vacancy_source or '—'}</span>"
    )


class FavoriteEventAdmin(ModelView, model=FavoriteEvent):
    name = "Событие избранного"
    name_plural = "История избранного"
    icon = "fa-solid fa-clock-rotate-left"

    column_list = [
        FavoriteEvent.id,
        FavoriteEvent.user_id,
        FavoriteEvent.action,
        FavoriteEvent.vacancy_name,
        FavoriteEvent.employer_name,
        FavoriteEvent.vacancy_source,
        FavoriteEvent.location,
        FavoriteEvent.category,
        FavoriteEvent.salary,
        FavoriteEvent.created_at,
    ]
    column_searchable_list = [
        FavoriteEvent.user_id,
        FavoriteEvent.vacancy_name,
        FavoriteEvent.employer_name,
        FavoriteEvent.location,
        FavoriteEvent.category,
    ]
    column_sortable_list = [FavoriteEvent.created_at, FavoriteEvent.action, FavoriteEvent.vacancy_source]
    column_default_sort = [(FavoriteEvent.created_at, True)]

    column_formatters = {
        FavoriteEvent.action: _fmt_fav_event_action,
        FavoriteEvent.vacancy_source: _fmt_fav_event_source,
    }
    column_formatters_detail = {
        FavoriteEvent.action: _fmt_fav_event_action,
        FavoriteEvent.vacancy_source: _fmt_fav_event_source,
    }

    can_create = False
    can_edit = False
    can_delete = False


class UserFavoritesView(BaseView):
    name = "Избранное по пользователям"
    icon = "fa-solid fa-users"
    engine = None  # устанавливается в create_admin перед add_base_view

    @expose("/user-favorites", methods=["GET"])
    async def user_favorites_page(self, request: Request) -> Response:
        user_id = request.query_params.get("user_id")

        async with AsyncSession(self.__class__.engine) as session:
            if user_id:
                # Детальная страница: вакансии конкретного пользователя
                rows = (await session.execute(
                    select(
                        FavoriteVacancies.vacancy_id,
                        FavoriteVacancies.vacancy_name,
                        FavoriteVacancies.employer_name,
                        FavoriteVacancies.vacancy_source,
                        FavoriteVacancies.location,
                        FavoriteVacancies.salary,
                        FavoriteVacancies.status,
                        FavoriteVacancies.updated_at,
                    )
                    .where(FavoriteVacancies.user_id == user_id)
                    .order_by(FavoriteVacancies.updated_at.desc())
                )).all()
                vacancies = [
                    {
                        "vacancy_id": r.vacancy_id,
                        "vacancy_name": r.vacancy_name,
                        "employer_name": r.employer_name,
                        "vacancy_source": r.vacancy_source,
                        "location": r.location,
                        "salary": r.salary,
                        "status": r.status,
                        "updated_at": r.updated_at,
                    }
                    for r in rows
                ]
                return await self.templates.TemplateResponse(
                    request,
                    "sqladmin/user_favorites_detail.html",
                    {
                        "title": "Избранное по пользователям",
                        "subtitle": f"Пользователь: {user_id}",
                        "user_id": user_id,
                        "vacancies": vacancies,
                    },
                )

            # Список всех пользователей
            user_rows = (await session.execute(
                select(
                    FavoriteVacancies.user_id,
                    func.count().label("cnt"),
                    func.max(FavoriteVacancies.updated_at).label("last_added"),
                )
                .group_by(FavoriteVacancies.user_id)
                .order_by(func.max(FavoriteVacancies.updated_at).desc())
            )).all()
            users = [
                {"user_id": r.user_id, "cnt": r.cnt, "last_added": r.last_added}
                for r in user_rows
            ]

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/user_favorites.html",
            {
                "title": "Избранное по пользователям",
                "subtitle": f"Уникальных пользователей: {len(users)}",
                "users": users,
            },
        )


class StatsView(BaseView):
    name = "Статистика"
    icon = "fa-solid fa-chart-bar"
    engine = None  # устанавливается в create_admin перед add_base_view

    @expose("/stats", methods=["GET"])
    async def stats_page(self, request: Request) -> Response:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=6)
        days_30_start = today_start - timedelta(days=29)

        async with AsyncSession(self.__class__.engine) as session:
            # ── API Keys ──
            total_keys = (await session.execute(
                select(func.count()).select_from(ApiKey)
            )).scalar_one()
            active_keys = (await session.execute(
                select(func.count()).select_from(ApiKey).where(ApiKey.is_active == True)  # noqa: E712
            )).scalar_one()
            keys_last_30d = (await session.execute(
                select(func.count()).select_from(ApiKey).where(ApiKey.created_at >= days_30_start)
            )).scalar_one()

            # ── SearchEvent ──
            searches_total = (await session.execute(
                select(func.count()).select_from(SearchEvent)
            )).scalar_one()
            searches_today = (await session.execute(
                select(func.count()).select_from(SearchEvent)
                .where(SearchEvent.created_at >= today_start)
            )).scalar_one()
            searches_week = (await session.execute(
                select(func.count()).select_from(SearchEvent)
                .where(SearchEvent.created_at >= week_start)
            )).scalar_one()
            errors_hh = (await session.execute(
                select(func.count()).select_from(SearchEvent).where(SearchEvent.error_hh == True)  # noqa: E712
            )).scalar_one()
            errors_tv = (await session.execute(
                select(func.count()).select_from(SearchEvent).where(SearchEvent.error_tv == True)  # noqa: E712
            )).scalar_one()
            top_locations_rows = (await session.execute(
                select(SearchEvent.location, func.count().label("cnt"))
                .group_by(SearchEvent.location)
                .order_by(func.count().desc())
                .limit(5)
            )).all()

            # ── AssistantSession ──
            sessions_total = (await session.execute(
                select(func.count()).select_from(AssistantSession)
            )).scalar_one()
            sessions_today = (await session.execute(
                select(func.count()).select_from(AssistantSession)
                .where(AssistantSession.created_at >= today_start)
            )).scalar_one()
            sessions_week = (await session.execute(
                select(func.count()).select_from(AssistantSession)
                .where(AssistantSession.created_at >= week_start)
            )).scalar_one()
            type_rows = (await session.execute(
                select(AssistantSession.session_type, func.count().label("cnt"))
                .group_by(AssistantSession.session_type)
                .order_by(func.count().desc())
            )).all()
            model_rows = (await session.execute(
                select(AssistantSession.llm_model, func.count().label("cnt"))
                .group_by(AssistantSession.llm_model)
                .order_by(func.count().desc())
            )).all()

            # ── FavoriteVacancies ──
            favorites_total = (await session.execute(
                select(func.count()).select_from(FavoriteVacancies)
            )).scalar_one()
            unique_users = (await session.execute(
                select(func.count(distinct(FavoriteVacancies.user_id)))
            )).scalar_one()
            favs_hh = (await session.execute(
                select(func.count()).select_from(FavoriteVacancies)
                .where(FavoriteVacancies.vacancy_source == "hh.ru")
            )).scalar_one()
            favs_tv = (await session.execute(
                select(func.count()).select_from(FavoriteVacancies)
                .where(FavoriteVacancies.vacancy_source == "trudvsem.ru")
            )).scalar_one()
            favs_not_found = (await session.execute(
                select(func.count()).select_from(FavoriteVacancies)
                .where(FavoriteVacancies.status == "not_found")
            )).scalar_one()

        _type_labels = {
            "cover_letter_by_vacancy": "Письмо по вакансии",
            "resume_tips_by_vacancy": "Советы по резюме (вакансия)",
            "letter_questionnaire": "Анкета для письма",
            "resume_questionnaire": "Анкета для резюме",
            "cover_letter_by_questionnaire": "Письмо по анкете",
            "resume_tips_by_questionnaire": "Советы по резюме (анкета)",
        }
        _type_colors = {
            "cover_letter_by_vacancy": "#F5B800",
            "resume_tips_by_vacancy": "#F5B800",
            "letter_questionnaire": "#3B82F6",
            "resume_questionnaire": "#3B82F6",
            "cover_letter_by_questionnaire": "#22C55E",
            "resume_tips_by_questionnaire": "#22C55E",
        }

        stats = {
            # API Keys
            "total_keys": total_keys,
            "active_keys": active_keys,
            "inactive_keys": total_keys - active_keys,
            "keys_last_30d": keys_last_30d,
            # SearchEvent
            "searches_total": searches_total,
            "searches_today": searches_today,
            "searches_week": searches_week,
            "errors_hh": errors_hh,
            "errors_tv": errors_tv,
            "top_locations": [{"location": r.location, "cnt": r.cnt} for r in top_locations_rows],
            # AssistantSession
            "sessions_total": sessions_total,
            "sessions_today": sessions_today,
            "sessions_week": sessions_week,
            "sessions_by_type": [
                {
                    "label": _type_labels.get(r.session_type, r.session_type),
                    "color": _type_colors.get(r.session_type, "#888"),
                    "cnt": r.cnt,
                }
                for r in type_rows
            ],
            "sessions_by_model": [{"model": r.llm_model, "cnt": r.cnt} for r in model_rows],
            # FavoriteVacancies
            "favorites_total": favorites_total,
            "unique_users": unique_users,
            "favs_hh": favs_hh,
            "favs_tv": favs_tv,
            "favs_not_found": favs_not_found,
        }

        return await self.templates.TemplateResponse(
            request,
            "sqladmin/stats.html",
            {"title": "Статистика", "subtitle": "Сводка по всем сервисам", "stats": stats},
        )
