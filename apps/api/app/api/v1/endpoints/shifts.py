from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AuthContext
from app.api.permissions import require_time_read

router = APIRouter()


@router.get("/")
async def list_shifts(
    _auth: AuthContext = Depends(require_time_read),
    location_id: str | None = Query(None),
) -> dict[str, list]:
    return {"items": []}