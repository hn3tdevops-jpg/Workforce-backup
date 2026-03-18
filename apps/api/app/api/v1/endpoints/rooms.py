from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext
from app.api.permissions import require_rooms_read

router = APIRouter()


@router.get("/")
async def list_rooms(
    _auth: AuthContext = Depends(require_rooms_read),
) -> dict[str, list]:
    return {"items": []}