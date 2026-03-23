# PROJECT KNOWLEDGE — Работа для всех

> **Дата последнего обновления:** 2026-03-22
> **Назначение:** Единый источник знаний о проекте для разработки с AI-агентами.
> Этот файл — истина в последней инстанции. При расхождении с другими документами доверять ему.

---

## Содержание

1. [Что такое проект](#1-что-такое-проект)
2. [Стек технологий](#2-стек-технологий)
3. [Архитектура и структура файлов](#3-архитектура-и-структура-файлов)
4. [Модели данных (БД)](#4-модели-данных-бд)
5. [API документация](#5-api-документация)
6. [Бизнес-логика и ключевые решения](#6-бизнес-логика-и-ключевые-решения)
7. [Фронтенд (план)](#7-фронтенд-план)
8. [Инфраструктура](#8-инфраструктура)
9. [Разработка: команды и настройка](#9-разработка-команды-и-настройка)
10. [Соглашения по коду](#10-соглашения-по-коду)
11. [Текущее состояние и задачи](#11-текущее-состояние-и-задачи)

---

## 1. Что такое проект

**REST API** для поиска вакансий в России, ориентированный на людей с инвалидностью и ограниченными возможностями.

**Что делает:**
- Агрегирует вакансии из двух внешних источников: **hh.ru** и **Работа России (trudvsem.ru)**
- Хранит вакансии в PostgreSQL и отдаёт через единый API
- Управляет **избранными вакансиями** пользователей с TTL-кэшированием
- Включает **AI-ассистента «Вера»** — генерирует сопроводительные письма и советы по резюме через Yandex LLM
- Имеет **веб-панель администратора** (sqladmin) для управления API-ключами и просмотра данных

**Целевые клиенты:** фронтенд-приложение (Next.js, в разработке), Telegram-боты, мобильные приложения.

**Язык кода, комментариев и документации:** русский.

---

## 2. Стек технологий

### Бэкенд

| Компонент | Технология |
|---|---|
| Фреймворк | FastAPI (async) |
| База данных | PostgreSQL |
| ORM | SQLAlchemy 2.0+ (async) |
| Миграции | Alembic |
| Валидация | Pydantic v2 |
| HTTP-клиент | httpx (async) |
| LLM | Yandex LLM API |
| Адмика | sqladmin |
| Линтинг | ruff |
| ASGI-сервер | Hypercorn |

### Фронтенд (планируется)

| Компонент | Технология |
|---|---|
| Фреймворк | Next.js 15 (App Router) |
| Язык | TypeScript |
| Компоненты | React Aria (headless, accessibility-first) |
| Стили | Tailwind CSS 4 |
| Серверное состояние | TanStack Query v5 |
| Формы | React Hook Form |
| Глобальный стейт | Zustand |

### Инфраструктура

| Компонент | Технология |
|---|---|
| Контейнеризация | Docker + Docker Compose |
| Reverse proxy | nginx |
| CI | GitHub Actions (существующий) |

---

## 3. Архитектура и структура файлов

### Слои приложения

```
Endpoint → Service → Repository → DB
                 ↘ External API (HH / TV / LLM)
```

**Правило:** каждый слой взаимодействует только со следующим. Эндпоинты не знают о репозиториях, сервисы не знают об эндпоинтах.

### Структура директорий

```
app/
├── admin/                        # Панель администратора (sqladmin)
│   ├── __init__.py               # Фабрика create_admin(app, engine)
│   ├── auth.py                   # Аутентификация по логин+пароль (ADMIN_LOGIN / ADMIN_PASSWORD)
│   └── views.py                  # ModelView: ApiKey, FavoriteVacancies, AssistantSession
│
├── api/v1/
│   ├── __init__.py               # Главный роутер v1, подключение всех под-роутеров
│   └── endpoints/
│       ├── api_keys.py           # Управление ключами (мастер-ключ)
│       ├── favorites.py          # Избранное
│       ├── federal_districts.py  # Справочник округов
│       ├── regions.py            # Справочник регионов
│       ├── vacancies.py          # Поиск и просмотр вакансий
│       └── vacancy_assistant.py  # AI-ассистент «Вера»
│
├── clients/
│   ├── hh_api_client.py          # HTTP-клиент hh.ru API
│   ├── tv_api_client.py          # HTTP-клиент trudvsem.ru API
│   └── llm.py                    # HTTP-клиент Yandex LLM API
│
├── core/
│   ├── settings.py               # Pydantic Settings: все env-переменные
│   └── config_logger.py          # Настройка логирования
│
├── db/
│   ├── models/
│   │   ├── base.py               # Декларативный Base
│   │   ├── base_vacancy.py       # Абстрактная BaseVacancy (28 полей)
│   │   ├── vacancies.py          # Таблица vacancies
│   │   ├── favorites.py          # Таблица favorite_vacancies (+ user_id, updated_at)
│   │   ├── api_keys.py           # Таблица api_keys
│   │   ├── assistant_session.py  # Таблица assistant_sessions
│   │   ├── search_event.py       # Таблица search_events (аналитика)
│   │   ├── regions.py            # Таблица regions
│   │   └── federal_districts.py  # Таблица federal_districts
│   ├── alembic/versions/         # 10+ миграций, последняя: add_search_events_table
│   └── session.py                # async_session_factory, engine
│
├── dependencies/
│   ├── api_key.py                # verify_api_key() — проверка X-Api-Key
│   ├── clients.py                # Dep-типы для HHClient, TVClient, LlmClient
│   ├── repositories.py           # Dep-типы для всех репозиториев
│   └── services.py               # Dep-типы VacanciesServiceDep, ApiKeyServiceDep
│
├── exceptions/                   # Кастомные исключения по слоям
│   ├── api_clients.py            # HHAPIRequestError, TVAPIRequestError, LLMAPIRequestError
│   ├── api_keys.py
│   ├── llm.py
│   ├── parsing_vacancies.py
│   ├── regions.py
│   ├── repositories.py           # FavoritesRepositoryError, VacanciesRepositoryError, ...
│   ├── services.py               # VacanciesServiceError, RegionServiceError
│   └── vacancies.py              # VacancyNotFoundError, VacanciesNotFoundError, VacancyAlreadyInFavoritesError
│
├── repositories/
│   ├── api_keys.py
│   ├── assistant_session.py
│   ├── favorites.py
│   ├── regions.py
│   ├── search_event.py
│   └── vacancies.py
│
├── schemas/
│   ├── api_key.py
│   ├── region.py
│   ├── vacancies.py              # VacancySchema (единая), VacanciesListSchema, ...
│   └── vacancy_assistant.py      # QuestionnaireResponseSchema, AssistantResultSchema
│
├── services/
│   ├── api_keys.py
│   ├── parsing_vacancies.py      # Парсеры HH / TV
│   ├── prompts/
│   │   └── assistant_vera.py     # LLM-промпты ассистента
│   ├── regions.py
│   ├── vacancies.py              # Основная бизнес-логика (~1100 строк)
│   └── vacancy_assistant.py      # Интеграция с LLM
│
├── static/                       # CSS для адмики
├── templates/                    # HTML-шаблоны (если нужны)
├── utils/
│   ├── check_db.py               # Проверка подключения к БД при старте
│   └── security.py               # Хеширование API-ключей
│
└── main.py                       # FastAPI app, lifespan, middleware, роутеры
```

---

## 4. Модели данных (БД)

### BaseVacancy (абстрактная, `__abstract__ = True`)

Все поля вакансии — унифицированы. Наследуется в `Vacancies` и `FavoriteVacancies`.

| Поле | Тип | Описание |
|---|---|---|
| `vacancy_id` | String(300) | ID вакансии на сайте-источнике |
| `vacancy_name` | Text | Название вакансии / должность |
| `location` | String(300) | Населённый пункт |
| `status` | String(50) | `actual`, `not_found` или NULL |
| `description` | Text | Описание обязанностей |
| `salary` | String(300) | Информация о зарплате |
| `vacancy_url` | Text | URL на сайте-источнике |
| `vacancy_source` | String(100) | `hh.ru` или `trudvsem.ru` |
| `employer_name` | Text | Наименование работодателя |
| `employer_location` | Text | Адрес работодателя |
| `employer_phone` | Text | Телефон работодателя |
| `employer_code` | String(100) | ID работодателя на источнике |
| `employer_email` | Text (nullable) | Email работодателя |
| `contact_person` | Text (nullable) | Контактное лицо |
| `employment` | Text (nullable) | Тип занятости |
| `schedule` | Text | График работы |
| `work_format` | Text (nullable) | Формат работы (офис / удалённо) |
| `experience_required` | Text | Требуемый опыт |
| `requirements` | Text (nullable) | Требования к кандидату |
| `category` | Text | Категория вакансии |
| `social_protected` | Text (nullable) | Признак для соц. защищённых |

> **Важно:** поля именованы как `vacancy_name`, `employment`, `employer_code` — везде единообразно (в моделях, схемах, парсерах). Никаких `name`, `employment_type`, `company_code`.

### Vacancies (таблица `vacancies`)

Наследует BaseVacancy. Временное хранилище — при каждом новом поиске по локации старые вакансии удаляются, новые записываются.

### FavoriteVacancies (таблица `favorite_vacancies`)

Наследует BaseVacancy. Долгосрочное хранилище.

| Дополнительное поле | Тип | Описание |
|---|---|---|
| `user_id` | String(300) | Внешний ID пользователя (email, Telegram ID и т.д.) |
| `updated_at` | DateTime(timezone=True) | Момент последнего обновления данных из источника |

Уникальный ключ: `(user_id, vacancy_id)`.

### ApiKey (таблица `api_keys`)

| Поле | Тип | Описание |
|---|---|---|
| `hashed_key` | String, unique | Хешированный ключ |
| `api_key_prefix` | String | Префикс для логов |
| `issued_for` | String | Описание клиента |
| `owner_email` | String | Email владельца |
| `comment` | Text | Внутренний комментарий |
| `created_at` | DateTime | Дата создания |
| `expires_at` | DateTime (nullable) | Дата истечения |
| `is_active` | Boolean | Флаг активности (soft-delete) |

### AssistantSession (таблица `assistant_sessions`)

Логирует каждый вызов AI-ассистента.

| Поле | Тип | Описание |
|---|---|---|
| `session_type` | String | Тип: `cover_letter_by_vacancy`, `cover_letter_by_questionnaire`, `letter_questionnaire`, `resume_tips_by_vacancy`, `resume_tips_by_questionnaire`, `resume_questionnaire` |
| `vacancy_id` | String | ID вакансии |
| `vacancy_name` | String | Название вакансии |
| `employer_name` / `employer_location` / `employment` / `salary` / `description` | String | Контекст вакансии |
| `answers` | JSONB (nullable) | Ответы пользователя на анкету |
| `result` | Text | HTML-результат от LLM |
| `llm_model` | String | Использованная модель |

### SearchEvent (таблица `search_events`)

Аналитика поисковых запросов. Таблица создана, интеграция в эндпоинты — в планах.

### Region / FederalDistricts

Справочники, загружаются при старте через `RegionService.initialize_region_data()` и кешируются в памяти.

---

## 5. API документация

### Аутентификация

Все эндпоинты (кроме `/api-keys/*`) требуют заголовок `X-Api-Key`.

```http
X-Api-Key: wfe_a1b2c3d4e5f6
```

| Код | Причина |
|---|---|
| `401` | Ключ отсутствует или не найден |
| `403` | Ключ просрочен или деактивирован |

Управление ключами — через `X-Master-Key` (значение из `MASTER_API_KEY` в env).

**Ошибки** всегда в формате `{ "detail": "Описание" }`.

---

### Федеральные округа `/api/v1/federal-districts`

#### `GET /api/v1/federal-districts/list`

Полный список федеральных округов.

**Ответ `200`:**
```json
[
  { "name": "Приволжский федеральный округ", "code": "33" }
]
```

| Код | Название |
|---|---|
| `30` | Центральный |
| `31` | Северо-Западный |
| `33` | Приволжский |
| `34` | Уральский |
| `38` | Северо-Кавказский |
| `40` | Южный |
| `41` | Сибирский |
| `42` | Дальневосточный |

---

### Регионы `/api/v1/regions`

#### `GET /api/v1/regions/list`

Все регионы России.

**Ответ `200`:** `RegionSchema[]`

```json
[{ "name": "Удмуртская Республика", "region_code": "18", "federal_district_code": "33" }]
```

#### `GET /api/v1/regions/by-federal-districts?federal_district_code=33`

Регионы по коду федерального округа.

**Ошибки:** `404` (округ не найден)

---

### Вакансии `/api/v1/vacancies`

#### `POST /api/v1/vacancies/search`

Загружает вакансии из hh.ru и trudvsem.ru, сохраняет в БД (предварительно удаляет старые по данной локации).

> Вызывать перед `/list` — формирует свежий срез.

**Тело запроса:**
```json
{ "region_code": "18", "location": "Ижевск" }
```

**Ответ `201`:**
```json
{
  "all_vacancies_count": 142,
  "vacancies_count_tv": 58,
  "vacancies_count_hh": 84,
  "error_request_hh": false,
  "error_request_tv": false,
  "error_details_hh": "",
  "error_details_tv": "",
  "location": "Ижевск",
  "region_name": "Удмуртская Республика"
}
```

> Если один из источников вернул ошибку — `error_request_hh/tv = true`, вакансии из второго источника всё равно сохраняются.

**Ошибки:** `400` (некорректный location), `404` (регион не найден)

---

#### `GET /api/v1/vacancies/list`

Пагинированный список сохранённых вакансий.

**Query-параметры:**

| Параметр | Тип | Обязателен | По умолчанию | Описание |
|---|---|---|---|---|
| `location` | string | Да | — | Название населённого пункта |
| `page` | int | Нет | `1` | Номер страницы (≥ 1) |
| `page_size` | int | Нет | `10` | Размер страницы (1–100) |
| `user_id` | string | Нет | null | ID пользователя. Если передан — заполняется `is_favorite` |
| `keyword` | string | Нет | null | Поиск по названию и описанию вакансии |
| `source` | string | Нет | null | Фильтр по источнику: `hh.ru` или `trudvsem.ru` |

**Ответ `200`:** `VacanciesListSchema`

```json
{
  "total": 42,
  "page": 1,
  "page_size": 10,
  "vacancies_count_hh": 30,
  "vacancies_count_tv": 12,
  "items": [{ /* VacancySchema */ }]
}
```

`vacancies_count_hh` и `vacancies_count_tv` — количество вакансий по каждому источнику с учётом всех переданных фильтров (`keyword`, `source`).

---

#### `GET /api/v1/vacancies/{vacancy_id}`

Детальная информация о вакансии.

**Query:** `user_id` (опционально) — если передан, заполняет `is_favorite`.

**Поведение:** для hh.ru пытается обогатить данные из API (краткий сниппет → полное описание), при ошибке возвращает данные из БД. Для trudvsem.ru — аналогично.

**Ответ `200`:** `VacancySchema`

**Ошибки:** `404` (вакансия не найдена)

---

### Избранное `/api/v1/favorites`

Избранное привязано к внешнему `user_id` — произвольной строке (email, Telegram ID и т.д.).

#### `POST /api/v1/favorites/add-vacancy`

Добавляет вакансию в избранное. При добавлении обогащает данные через API источника (hh.ru — полное описание).

**Тело:** `{ "user_id": "user_123", "vacancy_id": "12345" }`

**Ответ `201`:** `{ "message": "Вакансия с vacancy_id=12345 успешно добавлена в избранное." }`

**Ошибки:** `404` (вакансия не найдена), `409` (уже в избранном)

---

#### `POST /api/v1/favorites/delete-vacancy`

Удаляет вакансию из избранного.

**Тело:** `{ "user_id": "user_123", "vacancy_id": "12345" }`

**Ответ `204`** (без тела)

---

#### `GET /api/v1/favorites/list`

Список избранных вакансий с пагинацией. **Все элементы возвращаются с `is_favorite: true`.**

TTL-логика: если `updated_at < 24h` — данные из БД, иначе запрос к источнику → обновление в БД. При ошибке источника — возвращает snapshot из БД.

**Query:** `user_id` (обязателен), `page`, `page_size`

**Ответ `200`:** `FavoriteVacanciesListSchema`

> Если вакансия удалена на источнике — `status = "not_found"`, из избранного не удаляется.

---

#### `GET /api/v1/favorites/{vacancy_id}`

Детальная информация о конкретной вакансии из избранного. Та же TTL-логика. **Возвращается с `is_favorite: true`.**

**Query:** `user_id` (опционально) — ограничивает поиск избранным конкретного пользователя.

---

### AI Ассистент «Вера» `/api/v1/assistant`

Все эндпоинты работают с вакансиями из **избранного**. Результаты возвращаются как **HTML-строка** в поле `result`.

Два режима:
- **По вакансии** — быстрый шаблон без участия пользователя.
- **По анкете** — персонализированный: `questionnaire` → пользователь заполняет → `by-questionnaire`.

#### Сопроводительные письма

| Эндпоинт | Описание |
|---|---|
| `POST /cover-letter/{vacancy_id}` | Шаблонное письмо |
| `POST /cover-letter/questionnaire/{vacancy_id}` | Генерирует анкету (5–7 вопросов) |
| `POST /cover-letter/by-questionnaire/{vacancy_id}` | Персонализированное письмо по ответам |

#### Советы по резюме

| Эндпоинт | Описание |
|---|---|
| `POST /resume-tips/{vacancy_id}` | Советы по резюме |
| `POST /resume-tips/questionnaire/{vacancy_id}` | Генерирует анкету |
| `POST /resume-tips/by-questionnaire/{vacancy_id}` | Персонализированные советы по ответам |

**Тело `by-questionnaire`:**
```json
{
  "answers": [
    { "id": 1, "text": "Расскажите об опыте работы с клиентами.", "answer": "3 года в продажах." },
    { "id": 2, "text": "Почему вас привлекает эта вакансия?", "answer": "" }
  ]
}
```

**Ответ `200`:**
```json
{ "result": "<p>Уважаемый работодатель...</p>" }
```

---

### Управление API-ключами `/api/v1/api-keys`

Требуют `X-Master-Key`. **Не** требуют `X-Api-Key`.

| Эндпоинт | Описание |
|---|---|
| `GET /api-keys/list` | Список всех ключей |
| `POST /api-keys/create` | Создать новый ключ |
| `POST /api-keys/deactivate` | Деактивировать ключ |

---

### Панель администратора `/admin`

Веб-интерфейс sqladmin. Вход по логину и паролю (`ADMIN_LOGIN` / `ADMIN_PASSWORD` из env).

Разделы: API Keys, Избранное, Сессии ассистента.

---

## 6. Бизнес-логика и ключевые решения

### Схема данных — единая VacancySchema

Используется **везде**: список, детали, избранное, ответы AI-ассистента. Нет отдельных `VacancyOutSchema` и `VacancyDetailsOutSchema`.

| Поле | Тип | Примечание |
|---|---|---|
| `vacancy_id` | string | |
| `vacancy_name` | string | |
| `location` | string | |
| `vacancy_url` | string | |
| `vacancy_source` | string | `hh.ru` или `trudvsem.ru` |
| `status` | string | `""`, `"actual"`, `"not_found"` |
| `description` | string | |
| `salary` | string | |
| `employer_name` | string | |
| `employer_location` | string | |
| `employer_phone` | string | |
| `employer_code` | string | |
| `employer_email` | string | `""` если не указан |
| `contact_person` | string | `""` если не указан |
| `employment` | string | `""` если не указан |
| `schedule` | string | `""` если не указан |
| `work_format` | string | `""` если не указан |
| `experience_required` | string | `""` если не указан |
| `requirements` | string | `""` если не указан |
| `category` | string | `""` если не указан |
| `social_protected` | string | `""` если не указан |
| `is_favorite` | bool | `False` по умолчанию; `True` для избранного |

Поля с `""` по умолчанию вместо `null` — через `@field_validator(..., mode='before')`.

### Флаг is_favorite

- **В `/vacancies/list` и `/vacancies/{id}`**: выставляется только если передан `user_id`. Один батч-запрос `SELECT vacancy_id FROM favorite_vacancies WHERE user_id = ? AND vacancy_id IN (...)`.
- **В `/favorites/list` и `/favorites/{id}`**: всегда `True` — данные берутся из таблицы избранного.

### TTL-кэш в избранном (24 часа)

Поле `updated_at` в таблице `favorite_vacancies` отслеживает актуальность данных.

```
updated_at < 24h  →  возвращаем данные из БД (fast path)
updated_at ≥ 24h  →  запрос к источнику (HH/TV API):
    Успех           →  обновляем запись в БД, возвращаем свежие данные
    VacancyNotFound →  ставим status='not_found', обновляем updated_at, возвращаем с новым статусом
    API-ошибка      →  логируем, возвращаем snapshot из БД (не ломаем список)
```

Параллельность при обогащении списка ограничена `asyncio.Semaphore(5)`.

### Обогащение при добавлении в избранное

При `POST /favorites/add-vacancy` сервис:
1. Берёт вакансию из таблицы `vacancies`
2. Если источник hh.ru — запрашивает полное описание через API (в `vacancies` хранится только сниппет)
3. Сохраняет полный снимок в `favorite_vacancies`

При ошибке API — сохраняет данные из БД как есть.

### Иерархия методов в VacanciesService

```
Публичные методы сервиса:
  get_vacancies_by_location()      →  список с is_favorite
  get_vacancy_details()            →  деталь с обогащением из API + is_favorite
  add_vacancy_to_favorites()       →  добавление с обогащением
  delete_vacancy_from_favorites()
  get_user_favorites()             →  список с TTL-логикой
  get_vacancy_by_id_from_favorites()  →  деталь из избранного с TTL
  gen_cover_letter_by_vacancy()    →  AI
  gen_resume_tips_by_vacancy()     →  AI
  gen_letter_questionnaire()       →  AI
  gen_resume_questionnaire()       →  AI
  gen_cover_letter_by_questionnaire()  →  AI
  gen_resume_tips_by_questionnaire()   →  AI

Приватные:
  _fetch_vacancy_details_from_api(vacancy_id, vacancy_source, employer_code)
      →  _get_vacancy_details_hh_api()
      →  _get_vacancy_details_tv_api()
  _get_vacancy_by_id()             →  из таблицы vacancies
  _get_vacancy_by_id_from_favorites()  →  из избранного + TTL
  _fetch_one_favorite_vacancy()    →  одна вакансия из списка избранного + TTL
  _compile_enriched_favorite_vacancies()  →  параллельное обогащение списка
  _get_vacancies_data_from_apis()  →  параллельный сбор из HH + TV
  _get_vacancies_hh_api()
  _get_vacancies_tv_api()
```

---

## 7. Фронтенд (план)

Фронтенд **не реализован**. Ниже — спецификация для реализации.

Директория: `frontend/` (в корне проекта, рядом с `app/`).

### Страницы

| Маршрут | Описание |
|---|---|
| `/` | Форма поиска: выбор округа → региона → ввод города |
| `/vacancies?location=X&page=1` | Список вакансий с пагинацией и фильтрами |
| `/vacancies/[id]` | Детальная страница вакансии |
| `/favorites?user_id=X&page=1` | Избранные вакансии |

### Ключевое архитектурное решение — API-прокси

Фронтенд **никогда** не раскрывает `X-Api-Key` браузеру.

```
Браузер → GET /api/v1/...
        → API-роут Next.js (серверная сторона, добавляет X-Api-Key из env)
        → FastAPI
```

Реализация: `src/app/api/v1/[...path]/route.ts` — catch-all прокси.

### Идентификация пользователя

Пользователь не авторизуется в классическом смысле. `user_id` — произвольная строка, которую фронтенд хранит локально (например, в `localStorage`). Передаётся в запросы к `/vacancies/list` и `/favorites/*`.

### Стратегия доступности (screen reader first)

Целевая аудитория использует программы экранного доступа (NVDA, JAWS, VoiceOver).

**Обязательные требования:**

- `<html lang="ru">` в `layout.tsx`
- Уникальный `<title>` на каждой странице
- Skip-ссылка `<a href="#main-content">Перейти к содержимому</a>` — первый фокусируемый элемент
- Один `<header>`, один `<main id="main-content">`, один `<footer>`
- Ровно один `<h1>` на странице, без пропусков уровней
- После SPA-навигации — программный перевод фокуса на `<h1>` новой страницы
- Live-регионы `aria-live="polite"` для результатов поиска, добавления/удаления из избранного
- `role="alert"` (= `aria-live="assertive"`) только для ошибок API
- Кнопка «В избранное» — toggle: `aria-pressed`, `aria-label` с названием вакансии
- Список вакансий: `<ul role="list">` + `<li>` + `<article aria-labelledby="...">` + `<h2>`
- Форма: `<fieldset>` + `<legend>` для группы регион/округ; `aria-describedby` для ошибок
- Контрастность WCAG AA (4.5:1 текст, 3:1 крупный текст)

**Компоненты React Aria:** Button, Select/ComboBox, TextField, Link, Dialog/Modal, SearchField, Breadcrumbs.

**Тестирование:** `axe-core` (vitest-axe) в каждом unit-тесте, NVDA + Firefox вручную.

### Чеклист компонента

- [ ] Семантический HTML-тег
- [ ] Видимый `<label>` или `aria-label` у интерактивных элементов
- [ ] Клавиатурный доступ (Tab, Enter, Escape)
- [ ] Видимый индикатор фокуса (`focus-visible`)
- [ ] Screen reader объявляет состояние
- [ ] Динамические изменения через `aria-live`
- [ ] Иерархия заголовков не нарушена
- [ ] Контрастность ≥ 4.5:1
- [ ] Работает при zoom 200%
- [ ] axe-core без ошибок

---

## 8. Инфраструктура

### Текущий docker-compose.yml

Сервисы: `db` (PostgreSQL 16), `api_service` (FastAPI), `nginx`.

### Целевой docker-compose.yml (с фронтендом)

Добавляется сервис `frontend` (Next.js). nginx обновляется:
- `/` → frontend (:3000)
- `/api/` → api_service (:8000)
- `/docs`, `/openapi.json` → api_service

### nginx конфигурация (целевая)

```nginx
upstream api    { server api_service:8000; }
upstream frontend { server frontend:3000; }

server {
    listen 80;
    location /         { proxy_pass http://frontend; }
    location /_next/webpack-hmr { proxy_pass http://frontend; ... }  # только dev
    location /api/     { proxy_pass http://api; }
    location /docs     { proxy_pass http://api; }
    location /openapi.json { proxy_pass http://api; }
}
```

---

## 9. Разработка: команды и настройка

### Переменные окружения (.env)

```env
# База данных
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_NAME=...

# hh.ru API
ACCESS_TOKEN_HH=...

# Безопасность
MASTER_API_KEY=...        # Мастер-ключ для управления API-ключами
SECRET_KEY=...            # Секрет для сессий sqladmin

# Панель администратора
ADMIN_LOGIN=admin
ADMIN_PASSWORD=...

# LLM (Yandex)
LLM_API_KEY=...
LLM_API_URL=...
LLM_MODEL=...

# Фронтенд (после добавления)
API_KEY=...               # API-ключ для фронтенда
API_URL=http://api_service:8000
```

### Запуск

```bash
# Docker
docker-compose up --build

# Локально
pip install -r requirements.txt
hypercorn app.main:app --reload
```

### Миграции

```bash
# Применить все миграции
alembic upgrade head

# Создать новую миграцию (после изменений в models/)
alembic revision --autogenerate -m "Краткое описание"

# Откатить одну миграцию
alembic downgrade -1
```

> Файлы миграций создавать в `app/db/alembic/versions/`.
> Имя файла: `YYYYMMDD_HHmm_краткое_описание.py`.

### Линтинг

```bash
ruff check .
ruff check . --fix
```

---

## 10. Соглашения по коду

### Модели SQLAlchemy

1. **Наследование:** от `Base` (или от абстрактной модели типа `BaseVacancy`).
2. **Имя класса:** PascalCase. **Имя таблицы:** snake_case, множественное число.
3. **Документирование каждого поля** — обязательно:
   - `doc` — краткое описание для разработчика
   - `comment` — описание для БД (видно в DBeaver / DataGrip)
4. **`__repr__`** у каждой модели.
5. Внешние ключи с `ondelete='CASCADE'`.

```python
# Пример правильного поля
vacancy_name: Mapped[str] = mapped_column(
    Text,
    nullable=False,
    doc='Название вакансии.',
    comment='Название должности вакансии'
)
```

### Исключения

Трёхслойная система. Каждый слой бросает свои исключения:

```python
# Репозиторий
class VacanciesRepositoryError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    def __init__(self, error_details: str): ...
    @property
    def detail(self) -> str: return "A database error occurred..."

# Сервис
class VacanciesServiceError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    ...

# Клиент внешнего API
class HHAPIRequestError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    def __init__(self, error_details: str, request_url: str, request_params: dict = {}): ...
```

### Структура эндпоинта

```python
@router.get(
    path="/path",
    status_code=status.HTTP_200_OK,
    summary="Краткое описание",
    description="Подробное описание.",
    responses={
        200: {"description": "Успех."},
        404: {"description": "Не найдено."},
        500: {"description": "Ошибка сервера."},
    },
    response_model=ResponseSchema,
)
async def get_entity(
    service: ServiceDep,
    param: Annotated[str, Query(description="Описание параметра.")],
):
    """Docstring в стиле Google (Args, Returns, Raises)."""
    logger.info("🚀 Запрос GET /path. Параметр: %s.", param)
    try:
        result = await service.get_data(param=param)
        logger.info("✅ Запрос GET /path выполнен.")
        return result
    except (EntityRepositoryError, ServiceError) as error:
        logger.exception("❌ Ошибка GET /path. Параметр: %s. Детали: %s", param, error)
        raise HTTPException(status_code=error.status_code, detail=error.detail)
```

**Ключевые правила:**
- `logger.info()` в начале и конце успешного запроса
- `logger.exception()` при ошибке (включает traceback)
- `Annotated` + `Query`/`Path`/`Body` для параметров
- `try/except` только на конкретные кастомные исключения

### Логирование

Эмодзи-префиксы в логах (условное соглашение):
- 🚀 — начало обработки запроса
- ✅ — успешное завершение
- ❌ — ошибка
- ⚠️ — предупреждение (не критично)
- 🔍 — поиск / запрос к внешнему API
- 🔄 — обновление данных
- ➕ — добавление
- 🗑️ — удаление
- 📋 — получение списка
- 💾 — сохранение в БД
- 🤖 — AI-операция

---

## 11. Текущее состояние и задачи

### ✅ Реализовано и работает

**Бэкенд:**
- Загрузка вакансий из hh.ru и trudvsem.ru
- Хранение и поиск вакансий (пагинация, фильтр по keyword и source)
- Управление избранным с TTL-кэшированием (24 часа)
- Флаг `is_favorite` в списке и детальном просмотре вакансий
- AI-ассистент «Вера»: письма и советы по резюме (шаблонные + по анкете)
- Управление API-ключами (создание, деактивация, просмотр)
- Панель администратора (sqladmin, логин+пароль)
- Единая `VacancySchema` для всех ответов
- Унификация именования полей (`vacancy_name`, `employment`, `employer_code`)

**Инфраструктура:**
- Docker Compose (db + api_service + nginx)
- GitHub Actions CI (build + run)
- 10+ миграций Alembic

### 🔲 Не реализовано (следующие итерации)

**Фронтенд (итерация 2):**
- Весь Next.js фронтенд (план детально описан в разделе 7)
- Docker-сервис `frontend`
- Обновлённый nginx (проксирование фронтенда)

**Бэкенд:**
- Логирование SearchEvent в эндпоинты (таблица создана, интеграция нет)
- Rate limiting (slowapi подключен, правила не настроены)

### 📌 Известные ограничения

- `user_id` — не аутентифицированный идентификатор. Фронтенд сам генерирует/хранит. Безопасность через API-ключ (не через user_id).
- Вакансии в таблице `vacancies` — временные. При повторном поиске по той же локации удаляются и записываются заново.
- AI-ассистент работает только с вакансиями из **избранного** (нужен `vacancy_id` из `favorite_vacancies`).

---

*Документ поддерживается вручную. При изменениях в коде или планах обновлять соответствующие разделы здесь.*
