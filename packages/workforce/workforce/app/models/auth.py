"""
Auth-specific models: Role, user_roles association, and RefreshToken.

RefreshToken is defined in identity.py and re-exported here for convenience.
The existing Role model in employee.py covers the "Role (id UUID PK, name unique)" requirement;
this module adds an auth-scoped Role alias and the user↔role association table.
"""
from sqlalchemy import Column, ForeignKey, String, Table

from apps.api.app.models.base import Base, UUIDMixin
from apps.api.app.models.identity import RefreshToken  # noqa: F401 — re-export

# Re-export the existing scheduling Role for consumers who import from apps.api.app.models.auth
from apps.api.app.models.employee import Role  # noqa: F401

# ── User ↔ Auth-Role association ─────────────────────────────────────────────

# Many-to-many link between platform users and their global (non-tenant) roles.
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)
