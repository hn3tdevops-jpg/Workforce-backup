from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.db import get_db


def get_session(db: Session = Depends(get_db)) -> Generator[Session, None, None]:
    return db
