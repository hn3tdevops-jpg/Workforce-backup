from pydantic import BaseModel


class TaskRead(BaseModel):
    id: int
    title: str
    status: str
