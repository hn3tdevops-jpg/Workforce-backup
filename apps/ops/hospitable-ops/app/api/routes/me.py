from fastapi import APIRouter

router = APIRouter()

@router.get('/me/businesses')
async def my_businesses():
    return [{"id": "biz-1", "name": "Demo Business", "is_default": True}]
