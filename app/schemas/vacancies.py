from pydantic import BaseModel, Field


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
