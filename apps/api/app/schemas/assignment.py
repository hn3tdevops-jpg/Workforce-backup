from pydantic import BaseModel


class AssignmentRead(BaseModel):
    id: int
    task_id: int
    assigned_to_user_id: int
    status: str
