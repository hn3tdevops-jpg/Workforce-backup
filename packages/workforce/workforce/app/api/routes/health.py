from datetime import datetime, timezone

from fastapi import APIRouter

from apps.api.app.core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "env": settings.ENV, "time": datetime.now(timezone.utc).isoformat()}
