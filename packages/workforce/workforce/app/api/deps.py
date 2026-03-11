from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from apps.api.app.core.db import get_db
from apps.api.app.core.auth_deps import get_current_user  # noqa: F401 — re-export for Phase 2 interface


def get_session(db: Session = Depends(get_db)) -> Generator[Session, None, None]:
    return db
