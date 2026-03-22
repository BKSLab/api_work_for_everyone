from pydantic import BaseModel, ConfigDict, Field


class RegionSchema(BaseModel):
    """Схема региона для API-ответов (с маппингом кода trudvsem → region_code)."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description='Полное наименование субъекта РФ.', examples=['Удмуртская Республика'])
    region_code: str = Field(
        ...,
        validation_alias='code_tv',
        description='Код региона по классификатору trudvsem.ru.',
        examples=['18'],
    )
    federal_district_code: str = Field(
        ...,
        description='Код федерального округа.',
        examples=['PFO'],
    )


class RegionSchemaDb(BaseModel):
    """Схема региона с полными кодами для внутреннего использования (сервисы, репозитории)."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description='Полное наименование субъекта РФ.', examples=['Удмуртская Республика'])
    code_tv: str = Field(
        ...,
        description='Код региона по классификатору trudvsem.ru.',
        examples=['18'],
    )
    code_hh: str = Field(
        ...,
        description='Код региона по классификатору hh.ru.',
        examples=['1438'],
    )
    federal_district_code: str = Field(
        ...,
        description='Код федерального округа.',
        examples=['PFO'],
    )


class FederalDistrictSchema(BaseModel):
    """Схема федерального округа."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description='Полное наименование федерального округа.', examples=['Приволжский федеральный округ'])
    code: str = Field(..., description='Код федерального округа.', examples=['PFO'])
