from fastapi import APIRouter, Depends

from app.api.dependencies import AuthContext, require_permission

router = APIRouter()


@router.get("/")
async def list_tasks(
    _auth: AuthContext = Depends(require_permission("hk.tasks.manage")),
) -> dict[str, list]:
    return {"items": []}