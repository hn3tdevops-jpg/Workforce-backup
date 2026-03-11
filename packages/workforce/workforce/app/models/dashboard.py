"""
Dashboard models — widget definitions, templates, user layouts.
"""
import enum

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.models.base import Base, TimestampMixin, UUIDMixin


class WidgetType(str, enum.Enum):
    calendar         = "calendar"
    timeclock        = "timeclock"
    upcoming_shifts  = "upcoming_shifts"
    quick_stats      = "quick_stats"
    announcements    = "announcements"
    marketplace_feed = "marketplace_feed"
    custom_text      = "custom_text"


# Default icon + description per widget type
WIDGET_META = {
    "calendar":         {"icon": "bi-calendar3",        "title": "My Week Calendar",    "desc": "Weekly shift calendar"},
    "timeclock":        {"icon": "bi-stopwatch",         "title": "Time Clock",          "desc": "Clock in/out widget"},
    "upcoming_shifts":  {"icon": "bi-calendar-check",    "title": "Upcoming Shifts",     "desc": "Next scheduled shifts"},
    "quick_stats":      {"icon": "bi-bar-chart-line",    "title": "Quick Stats",         "desc": "Key metrics at a glance"},
    "announcements":    {"icon": "bi-megaphone",         "title": "Announcements",       "desc": "Custom announcement text"},
    "marketplace_feed": {"icon": "bi-briefcase",         "title": "Job Board Feed",      "desc": "Open job postings"},
    "custom_text":      {"icon": "bi-card-text",         "title": "Custom Text",         "desc": "Free-form text/HTML block"},
}


class WidgetDefinition(UUIDMixin, TimestampMixin, Base):
    """
    A widget definition — system-built or admin-created.
    System widgets (is_system=True) cannot be deleted.
    business_id=NULL means global (available everywhere).
    """
    __tablename__ = "widget_definitions"

    business_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str] = mapped_column(String(60), nullable=False, default="bi-grid")
    default_config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_widget_def_business", "business_id"),
    )


class DashboardTemplate(UUIDMixin, TimestampMixin, Base):
    """
    A named dashboard layout that admins can assign to users.
    layout_json: JSON list of widget slots [{slot_id, type, w, title, config}]
    """
    __tablename__ = "dashboard_templates"

    business_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True
    )
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    layout_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_dashboard_template_biz", "business_id"),
    )


class UserDashboard(UUIDMixin, TimestampMixin, Base):
    """
    Per-user dashboard configuration for a specific business.
    layout_json overrides the template if set.
    is_locked=True means the user cannot edit their layout.
    """
    __tablename__ = "user_dashboards"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("dashboard_templates.id", ondelete="SET NULL"), nullable=True
    )
    layout_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # user overrides
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_user_dashboard"),
        Index("ix_user_dashboard_biz", "business_id"),
    )
