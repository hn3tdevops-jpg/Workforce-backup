from sqlalchemy import Column, String, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship
from apps.api.app.db.session import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", String, ForeignKey("permissions.id"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"
    id = Column(String, primary_key=True)
    business_id = Column(String, nullable=False)
    scope_type = Column(String, nullable=False)
    location_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    priority = Column(Integer, default=0)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    business_id = Column(String, nullable=False)
    scope_type = Column(String, nullable=False)
    location_id = Column(String, nullable=True)
    role_id = Column(String, ForeignKey("roles.id"), nullable=False)
    job_title_label = Column(String, nullable=True)
    created_by_user_id = Column(String, nullable=True)
