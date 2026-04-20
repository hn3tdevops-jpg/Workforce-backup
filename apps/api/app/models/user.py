import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# Re-export canonical User model from packages.workforce
from packages.workforce.workforce.app.models.identity import User  # noqa: F401
__all__ = ["User"]
