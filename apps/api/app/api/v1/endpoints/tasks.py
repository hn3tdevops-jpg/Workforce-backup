from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tasks() -> dict[str, list]:
    return {"items": []}
