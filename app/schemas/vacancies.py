from pydantic import BaseModel, ConfigDict, Field, field_validator


class VacanciesSearchRequest(BaseModel):
    """Тело запроса для поиска и сохранения вакансий."""

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'region_code': '18',
                'location': 'Ижевск',
            }
        }
    )

    region_code: str = Field(
        ...,
        description='Код региона (код субъекта РФ по классификатору trudvsem.ru).',
        examples=['18'],
    )
    location: str = Field(
        ...,
        description='Наименование населённого пункта для поиска вакансий.',
        examples=['Ижевск'],
    )


class VacanciesInfoSchema(BaseModel):
    """Результат поиска и сохранения вакансий — статистика по источникам."""

    all_vacancies_count: int = Field(
        ...,
        description='Общее количество сохранённых вакансий по двум источникам.',
        examples=[142],
    )
    vacancies_count_tv: int = Field(
        ...,
        description='Количество вакансий из trudvsem.ru.',
        examples=[58],
    )
    vacancies_count_hh: int = Field(
        ...,
        description='Количество вакансий из hh.ru.',
        examples=[84],
    )
    error_request_hh: bool = Field(
        ...,
        description='Флаг ошибки при запросе к hh.ru.',
        examples=[False],
    )
    error_request_tv: bool = Field(
        ...,
        description='Флаг ошибки при запросе к trudvsem.ru.',
        examples=[False],
    )
    error_details_hh: str = Field(
        ...,
        description='Детали ошибки hh.ru (пустая строка если ошибки не было).',
        examples=[''],
    )
    error_details_tv: str = Field(
        ...,
        description='Детали ошибки trudvsem.ru (пустая строка если ошибки не было).',
        examples=[''],
    )
    location: str = Field(
        ...,
        description='Нормализованное наименование населённого пункта.',
        examples=['Ижевск'],
    )
    region_name: str = Field(
        ...,
        description='Полное название региона.',
        examples=['Удмуртская Республика'],
    )


class VacancySchema(BaseModel):
    """Единая схема вакансии для списка, избранного и детального просмотра."""

    model_config = ConfigDict(from_attributes=True)

    vacancy_id: str = Field(
        ...,
        description='Идентификатор вакансии на сайте-источнике.',
        examples=['12345'],
    )
    vacancy_name: str = Field(
        ...,
        description='Название вакансии / должность.',
        examples=['Python-разработчик'],
    )
    location: str = Field(
        ...,
        description='Город или населённый пункт, где расположена вакансия.',
        examples=['Ижевск'],
    )
    vacancy_url: str = Field(
        ...,
        description='Полный URL вакансии на сайте-источнике.',
        examples=['https://hh.ru/vacancy/12345'],
    )
    vacancy_source: str = Field(
        ...,
        description='Источник вакансии.',
        examples=['hh.ru', 'trudvsem.ru'],
    )
    status: str = Field(
        '',
        description='Статус вакансии: actual, not_found.',
        examples=['actual'],
    )
    description: str = Field(
        ...,
        description='Полное описание обязанностей и требований.',
        examples=['Разработка backend-сервисов на Python и FastAPI.'],
    )
    salary: str = Field(
        ...,
        description='Информация о заработной плате.',
        examples=['от 150 000 руб.'],
    )
    employer_name: str = Field(
        ...,
        description='Наименование компании-работодателя.',
        examples=['ООО Рога и Копыта'],
    )
    employer_location: str = Field(
        ...,
        description='Адрес работодателя.',
        examples=['г. Ижевск, ул. Пушкинская, 1'],
    )
    employer_phone: str = Field(
        ...,
        description='Контактный телефон работодателя.',
        examples=['+7 (3412) 12-34-56'],
    )
    employer_code: str = Field(
        ...,
        description='Идентификатор работодателя на сайте-источнике.',
        examples=['9876'],
    )
    employer_email: str = Field(
        '',
        description='Контактный email работодателя.',
        examples=['hr@example.com'],
    )
    contact_person: str = Field(
        '',
        description='ФИО контактного лица.',
        examples=['Иванова Анна Петровна'],
    )
    employment: str = Field(
        '',
        description='Тип занятости.',
        examples=['Полная занятость'],
    )
    schedule: str = Field(
        '',
        description='График работы.',
        examples=['Полный день'],
    )
    work_format: str = Field(
        '',
        description='Формат работы: офис, удалённо, разъездной и т.д.',
        examples=['Офис'],
    )
    experience_required: str = Field(
        '',
        description='Требуемый опыт работы.',
        examples=['1–3 года'],
    )
    requirements: str = Field(
        '',
        description='Конкретные требования к кандидату: навыки, знания.',
        examples=['Python, FastAPI, PostgreSQL'],
    )
    category: str = Field(
        '',
        description='Категория вакансии.',
        examples=['Информационные технологии'],
    )
    social_protected: str = Field(
        '',
        description='Признак вакансии для социально защищённых категорий граждан.',
        examples=[''],
    )
    is_favorite: bool = Field(
        False,
        description='Признак добавления вакансии в избранное текущим пользователем.',
        examples=[False],
    )

    @field_validator(
        'status', 'employer_email', 'contact_person',
        'work_format', 'requirements', 'social_protected',
        mode='before',
    )
    @classmethod
    def none_to_empty_string(cls, v: object) -> str:
        return '' if v is None else v


class VacanciesListSchema(BaseModel):
    """Пагинированный список вакансий по населённому пункту."""

    total: int = Field(..., description='Общее количество вакансий, удовлетворяющих фильтрам.', examples=[142])
    page: int = Field(..., description='Текущий номер страницы.', examples=[1])
    page_size: int = Field(..., description='Количество вакансий на странице.', examples=[10])
    items: list[VacancySchema] = Field(..., description='Список вакансий на текущей странице.')


class FavoriteVacanciesListSchema(BaseModel):
    """Пагинированный список избранных вакансий пользователя."""

    total: int = Field(..., description='Общее количество вакансий в избранном.', examples=[25])
    page: int = Field(..., description='Текущий номер страницы.', examples=[1])
    page_size: int = Field(..., description='Количество вакансий на странице.', examples=[10])
    items: list[VacancySchema] = Field(..., description='Список избранных вакансий на текущей странице.')


class VacancyAddFavoriteSchema(BaseModel):
    """Тело запроса для добавления или удаления вакансии из избранного."""

    user_id: str = Field(
        ...,
        description='Идентификатор пользователя во внешней системе (Telegram ID, email и т.д.).',
        examples=['user_123'],
    )
    vacancy_id: str = Field(
        ...,
        description='Идентификатор вакансии на сайте-источнике.',
        examples=['12345'],
    )


class MsgSchema(BaseModel):
    """Простой ответ с текстовым сообщением."""

    message: str = Field(..., description='Текст сообщения об успешном выполнении операции.')
