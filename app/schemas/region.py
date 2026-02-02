from pydantic import BaseModel, ConfigDict


class RegionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    code_tv: str
    code_hh: str
    federal_district_code: str


class FederalDistrictSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str
    code: str
