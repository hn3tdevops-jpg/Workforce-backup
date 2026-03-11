from typing import List
from dataclasses import dataclass

@dataclass
class Role:
    id: str
    name: str
    permissions: List[str]

# Simple in-memory placeholder for skeleton
ROLES = {}

def create_role(role_id: str, name: str, permissions: List[str]):
    ROLES[role_id] = Role(id=role_id, name=name, permissions=permissions)
    return ROLES[role_id]

def role_has_permission(role_id: str, permission: str) -> bool:
    role = ROLES.get(role_id)
    return role and (permission in role.permissions)
