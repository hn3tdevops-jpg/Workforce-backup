"""
TimeEntry model for the dynamic timeclock system.
"""
import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from packages.workforce.workforce.app.models.base import Base, TimestampMixin, UUIDMixin


class TimeEntryStatus(str, enum.Enum):
    active    = "active"      # currently clocked in
    completed = "completed"   # clocked out, awaiting review
    approved  = "approved"    # manager approved
    disputed  = "disputed"    # manager flagged for review


class TimeEntry(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "time_entries"

    user_id:        Mapped[str]       = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id:    Mapped[str]       = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id:    Mapped[str|None]  = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    clocked_in_at:  Mapped[str]       = mapped_column(DateTime(timezone=True), nullable=False)
    clocked_out_at: Mapped[str|None]  = mapped_column(DateTime(timezone=True), nullable=True)
    total_minutes:  Mapped[float|None]= mapped_column(Float, nullable=True)   # computed on clock-out
    notes:          Mapped[str|None]  = mapped_column(Text, nullable=True)
    status: Mapped[TimeEntryStatus]   = mapped_column(
        Enum(TimeEntryStatus, name="time_entry_status"),
        nullable=False, default=TimeEntryStatus.active
    )
