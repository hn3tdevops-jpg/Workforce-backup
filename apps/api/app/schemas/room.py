from pydantic import BaseModel


class RoomRead(BaseModel):
    id: int
    room_number: str
    status: str
