from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext
from app.api.permissions import require_time_read

router = APIRouter()


@router.get("/")
async def list_shifts(
    _auth: AuthContext = Depends(require_time_read),
) -> dict[str, list]:
    return {"items": []}