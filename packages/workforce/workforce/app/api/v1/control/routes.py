"""
Control plane routes (superadmin only).
Tenant CRUD, global audit log, agent registry.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import SuperAdmin
from apps.api.app.core.db import get_db
from apps.api.app.core.security import generate_api_key
from apps.api.app.models.business import Business
from apps.api.app.models.identity import (
    Agent, AgentCredential, AgentStatus, AgentType,
    AuditEvent, BizRole, BizRolePermission, Permission, User, UserStatus,
)
from apps.api.app.services.roles_seed import provision_business_defaults, seed_permissions_and_roles

router = APIRouter(prefix="/api/v1/control", tags=["control"])


# ── Tenants ───────────────────────────────────────────────────────────────────

class BusinessCreate(BaseModel):
    name: str
    plan: str = "free"
    settings: dict = {}


@router.get("/businesses")
def list_businesses(_: SuperAdmin, db: Session = Depends(get_db)):
    rows = db.execute(select(Business).where(Business.deleted_at == None)).scalars().all()  # noqa: E711
    return [{"id": b.id, "name": b.name, "plan": b.plan} for b in rows]


@router.post("/businesses", status_code=201)
def create_business(payload: BusinessCreate, _: SuperAdmin, db: Session = Depends(get_db)):
    biz = Business(
        name=payload.name,
        plan=payload.plan,
        settings_json=json.dumps(payload.settings),
    )
    db.add(biz)
    db.commit()
    db.refresh(biz)
    provision_business_defaults(biz.id, db)
    return {"id": biz.id, "name": biz.name, "plan": biz.plan}


@router.delete("/businesses/{business_id}", status_code=204)
def soft_delete_business(business_id: str, _: SuperAdmin, db: Session = Depends(get_db)):
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(404, "Business not found")
    biz.deleted_at = datetime.now(timezone.utc)
    db.commit()


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit")
def global_audit(
    _: SuperAdmin,
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    rows = db.execute(
        select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit).offset(offset)
    ).scalars().all()
    return [
        {
            "id": e.id,
            "business_id": e.business_id,
            "actor_type": e.actor_type,
            "actor_id": e.actor_id,
            "action": e.action,
            "entity": e.entity,
            "entity_id": e.entity_id,
            "created_at": e.created_at,
            "correlation_id": e.correlation_id,
        }
        for e in rows
    ]


# ── Users (control view) ──────────────────────────────────────────────────────

@router.get("/users")
def list_users(_: SuperAdmin, db: Session = Depends(get_db)):
    rows = db.execute(select(User)).scalars().all()
    return [{"id": u.id, "email": u.email, "status": u.status, "is_superadmin": u.is_superadmin} for u in rows]


@router.patch("/users/{user_id}/status")
def set_user_status(user_id: str, status: str, _: SuperAdmin, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    try:
        user.status = UserStatus(status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {status}")
    db.commit()
    return {"id": user.id, "status": user.status}


# ── Agent registry ────────────────────────────────────────────────────────────

class AgentCreate(BaseModel):
    name: str
    type: str = "service"
    business_id: Optional[str] = None
    scopes: list[str] = ["*"]
    expires_days: Optional[int] = None


@router.get("/agents")
def list_agents(_: SuperAdmin, db: Session = Depends(get_db)):
    rows = db.execute(select(Agent)).scalars().all()
    return [
        {"id": a.id, "name": a.name, "type": a.type, "status": a.status, "business_id": a.business_id}
        for a in rows
    ]


@router.post("/agents", status_code=201)
def create_agent(payload: AgentCreate, _: SuperAdmin, db: Session = Depends(get_db)):
    try:
        agent_type = AgentType(payload.type)
    except ValueError:
        raise HTTPException(400, f"Invalid agent type: {payload.type}")

    agent = Agent(
        name=payload.name,
        type=agent_type,
        business_id=payload.business_id,
        status=AgentStatus.active,
    )
    db.add(agent)
    db.flush()

    full_key, prefix, key_hash = generate_api_key()
    expires_at = None
    if payload.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_days)

    cred = AgentCredential(
        agent_id=agent.id,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes_json=json.dumps(payload.scopes),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(cred)
    db.commit()
    db.refresh(agent)
    # Return the key once — not stored in plaintext
    return {
        "id": agent.id,
        "name": agent.name,
        "api_key": full_key,  # shown once only
        "key_prefix": prefix,
    }


@router.delete("/agents/{agent_id}", status_code=204)
def revoke_agent(agent_id: str, _: SuperAdmin, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    agent.status = AgentStatus.revoked
    # Revoke all credentials
    creds = db.execute(
        select(AgentCredential).where(AgentCredential.agent_id == agent_id)
    ).scalars().all()
    for c in creds:
        c.revoked = True
    db.commit()


# ── Permissions registry ──────────────────────────────────────────────────────

@router.get("/permissions")
def list_permissions(_: SuperAdmin, db: Session = Depends(get_db)):
    """Return all registered permissions, grouped by module."""
    rows = db.execute(select(Permission).order_by(Permission.key)).scalars().all()
    groups: dict[str, list] = {}
    for p in rows:
        module = p.key.split(":")[0]
        groups.setdefault(module, []).append({"id": p.id, "key": p.key, "description": p.description})
    return {"groups": groups, "total": len(rows)}


# ── System-template roles CRUD ────────────────────────────────────────────────

def _role_detail(role: BizRole, db: Session) -> dict:
    perms = db.execute(
        select(Permission)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .where(BizRolePermission.role_id == role.id)
        .order_by(Permission.key)
    ).scalars().all()
    return {
        "id": role.id,
        "name": role.name,
        "is_system_template": role.is_system_template,
        "business_id": role.business_id,
        "permissions": [{"id": p.id, "key": p.key, "description": p.description} for p in perms],
    }


@router.get("/roles")
def list_roles(_: SuperAdmin, db: Session = Depends(get_db)):
    rows = db.execute(
        select(BizRole)
        .where(BizRole.is_system_template == True)  # noqa: E712
        .order_by(BizRole.name)
    ).scalars().all()
    return [_role_detail(r, db) for r in rows]


class RoleCreate(BaseModel):
    name: str
    permission_keys: list[str] = []


@router.post("/roles", status_code=201)
def create_role(payload: RoleCreate, _: SuperAdmin, db: Session = Depends(get_db)):
    existing = db.execute(
        select(BizRole).where(BizRole.name == payload.name, BizRole.is_system_template == True)  # noqa: E712
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, f"System role '{payload.name}' already exists")

    role = BizRole(name=payload.name, is_system_template=True, business_id=None)
    db.add(role)
    db.flush()

    for pkey in payload.permission_keys:
        perm = db.execute(select(Permission).where(Permission.key == pkey)).scalar_one_or_none()
        if not perm:
            perm = Permission(key=pkey)
            db.add(perm)
            db.flush()
        db.add(BizRolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
    db.refresh(role)
    return _role_detail(role, db)


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    permission_keys: list[str]  # full replacement — send complete desired set


@router.put("/roles/{role_id}")
def update_role(role_id: str, payload: RoleUpdate, _: SuperAdmin, db: Session = Depends(get_db)):
    role = db.get(BizRole, role_id)
    if not role or not role.is_system_template:
        raise HTTPException(404, "System role not found")

    if payload.name is not None:
        # Check uniqueness
        conflict = db.execute(
            select(BizRole).where(
                BizRole.name == payload.name,
                BizRole.is_system_template == True,  # noqa: E712
                BizRole.id != role_id,
            )
        ).scalar_one_or_none()
        if conflict:
            raise HTTPException(400, f"Role name '{payload.name}' already in use")
        role.name = payload.name

    # Replace permission set
    db.execute(
        BizRolePermission.__table__.delete().where(BizRolePermission.role_id == role_id)
    )
    db.flush()

    for pkey in payload.permission_keys:
        perm = db.execute(select(Permission).where(Permission.key == pkey)).scalar_one_or_none()
        if not perm:
            perm = Permission(key=pkey)
            db.add(perm)
            db.flush()
        db.add(BizRolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
    db.refresh(role)
    return _role_detail(role, db)


@router.delete("/roles/{role_id}", status_code=204)
def delete_role(role_id: str, _: SuperAdmin, db: Session = Depends(get_db)):
    role = db.get(BizRole, role_id)
    if not role or not role.is_system_template:
        raise HTTPException(404, "System role not found")
    db.execute(
        BizRolePermission.__table__.delete().where(BizRolePermission.role_id == role_id)
    )
    db.delete(role)
    db.commit()


@router.post("/roles/seed")
def seed_roles(_: SuperAdmin, db: Session = Depends(get_db)):
    """Idempotently seed default permissions and system-template roles."""
    return seed_permissions_and_roles(db)
