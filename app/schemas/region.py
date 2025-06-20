from pydantic import BaseModel, ConfigDict


class RegionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    region_name: str
    region_code_tv: str
    region_code_hh: str
    federal_district_code: str


class FederalDistrictSchema(BaseModel):
    federal_district_name: str
    federal_district_code: str
