from pydantic import BaseModel


class ShiftRead(BaseModel):
    id: int
    title: str
    status: str
