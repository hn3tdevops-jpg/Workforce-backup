from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_assignments() -> dict[str, list]:
    return {"items": []}
