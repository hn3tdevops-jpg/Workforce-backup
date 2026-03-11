from sqlalchemy import Table, Column, String, Integer, ForeignKey
from sqlalchemy.orm import registry

mapper_registry = registry()

metadata = mapper_registry.metadata

roles = Table(
    "roles",
    metadata,
    Column("id", String, primary_key=True),
    Column("business_id", String, nullable=False),
    Column("scope_type", String, nullable=False),
    Column("location_id", String, nullable=True),
    Column("name", String, nullable=False),
    Column("priority", Integer, default=0),
)

permissions = Table(
    "permissions",
    metadata,
    Column("id", String, primary_key=True),
    Column("key", String, unique=True, nullable=False),
)

role_permissions = Table(
    "role_permissions",
    metadata,
    Column("role_id", String, ForeignKey("roles.id")),
    Column("permission_id", String, ForeignKey("permissions.id")),
)
