from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AuthContext
from app.api.permissions import require_tasks_manage

router = APIRouter()


@router.get("/")
async def list_tasks(
    _auth: AuthContext = Depends(require_tasks_manage),
    location_id: str | None = Query(None),
) -> dict[str, list]:
    return {"items": []}