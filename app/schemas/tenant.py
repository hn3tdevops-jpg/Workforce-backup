import uuid

from pydantic import BaseModel, ConfigDict


class BusinessCreate(BaseModel):
    name: str
    settings_json: dict | None = None


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    settings_json: dict | None = None


class LocationCreate(BaseModel):
    name: str
    business_id: uuid.UUID
    settings_json: dict | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    business_id: uuid.UUID
    name: str
    settings_json: dict | None = None
