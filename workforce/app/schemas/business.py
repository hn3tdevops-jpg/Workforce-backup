from pydantic import BaseModel


class BusinessCreate(BaseModel):
    name: str


class BusinessRead(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class LocationCreate(BaseModel):
    name: str
    timezone: str = "UTC"
    parent_id: str | None = None


class LocationRead(BaseModel):
    id: str
    business_id: str
    parent_id: str | None
    name: str
    timezone: str

    model_config = {"from_attributes": True}


class LocationWithChildrenRead(LocationRead):
    children: list["LocationRead"] = []

    model_config = {"from_attributes": True}
