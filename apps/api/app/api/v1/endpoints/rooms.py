from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_rooms() -> dict[str, list]:
    return {"items": []}
