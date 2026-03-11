from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter()

_BOOTSTRAP_DONE = False


class BootstrapRequest(BaseModel):
    admin_email: EmailStr
    admin_password: str
    business_name: str
    location_name: str


@router.post("", status_code=status.HTTP_201_CREATED)
async def bootstrap(payload: BootstrapRequest) -> dict[str, object]:
    global _BOOTSTRAP_DONE

    if _BOOTSTRAP_DONE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap already completed",
        )

    _BOOTSTRAP_DONE = True

    return {
        "business_id": 1,
        "location_id": 1,
        "user_id": 1,
        "admin_email": payload.admin_email,
        "business_name": payload.business_name,
        "location_name": payload.location_name,
        "created": True,
    }
