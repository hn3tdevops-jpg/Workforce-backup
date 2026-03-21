from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext
from app.api.permissions import require_schedule_read

router = APIRouter()


@router.get("/")
async def list_assignments(
    _auth: AuthContext = Depends(require_schedule_read),
) -> dict[str, list]:
    return {"items": []}