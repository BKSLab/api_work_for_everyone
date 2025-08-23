from pydantic import BaseModel, ConfigDict, Field


class VacanciesSearchRequest(BaseModel):
    region_code: str = Field(..., description='Код региона')
    location: str = Field(..., description='Наименование населенного пункта')

    class Config:
        json_schema_extra = {
            'example': {
                'region_code': '18',
                'location': 'Ижевск'
            }
        }


class VacanciesInfoSchema(BaseModel):
    all_vacancies_count: int
    vacancies_count_tv: int
    vacancies_count_hh: int
    location: str
    region_name: str


class VacancyOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    vacancy_id: str
    location: str
    name: str
    description: str
    salary: str
    vacancy_url: str
    vacancy_source: str
    employer_name: str
    employer_location: str
    employer_phone: str
    employer_code: str
    experience_required: str
    category: str
    employment_type: str
    schedule: str


class VacanciesListSchema(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[VacancyOutSchema]


class VacancyDetailsOutSchema(BaseModel):
    vacancy_name: str
    vacancy_id: str
    vacancy_url: str
    social_protected: str
    vacancy_source: str
    description: str
    employer_location: str
    salary: str
    employer_name: str
    company_code: str
    employer_phone: str
    employer_email: str
    contact_person: str
    employment: str
