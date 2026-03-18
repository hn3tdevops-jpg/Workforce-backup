from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext
from app.api.permissions import require_tasks_manage

router = APIRouter()


@router.get("/")
async def list_tasks(
    _auth: AuthContext = Depends(require_tasks_manage),
) -> dict[str, list]:
    return {"items": []}