from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext, require_permission

router = APIRouter()


@router.get("/")
async def list_rooms(
    _auth: AuthContext = Depends(require_permission("hk.rooms.read")),
):
    ...
