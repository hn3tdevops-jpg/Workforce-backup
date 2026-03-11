from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_shifts() -> dict[str, list]:
    return {"items": []}
