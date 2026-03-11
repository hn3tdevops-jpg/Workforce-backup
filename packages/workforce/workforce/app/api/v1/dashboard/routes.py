"""
Dashboard API — widget definitions, templates, user layouts.
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, SuperAdmin, require_permission
from apps.api.app.core.db import get_db
from apps.api.app.models.dashboard import (
    DashboardTemplate, UserDashboard, WidgetDefinition
)
from apps.api.app.models.identity import BizRole, BizRolePermission, Membership, MembershipStatus, Permission, User

# ── Routers ───────────────────────────────────────────────────────────────────
control_router = APIRouter(prefix="/api/v1/control", tags=["control-dashboard"])
tenant_router  = APIRouter(prefix="/api/v1/tenant/{business_id}", tags=["tenant-dashboard"])
worker_router  = APIRouter(prefix="/api/v1/worker", tags=["worker-dashboard"])


# ── Helpers ───────────────────────────────────────────────────────────────────

DEFAULT_LAYOUT = [
    {"slot": "s1", "type": "quick_stats",     "w": 12, "title": "Quick Stats",     "config": {}},
    {"slot": "s2", "type": "upcoming_shifts", "w": 8,  "title": "Upcoming Shifts", "config": {}},
    {"slot": "s3", "type": "timeclock",       "w": 4,  "title": "Time Clock",      "config": {}},
    {"slot": "s4", "type": "calendar",        "w": 12, "title": "My Week",         "config": {}},
]

SUPERADMIN_LAYOUT = [
    {"slot": "s1", "type": "quick_stats",     "w": 12, "title": "Platform Stats",  "config": {}},
    {"slot": "s2", "type": "calendar",        "w": 12, "title": "Schedule",        "config": {}},
]


def _effective_layout(ud: UserDashboard | None, template: DashboardTemplate | None, is_superadmin=False) -> list:
    """Return the effective layout for a user dashboard."""
    if ud and ud.layout_json:
        return json.loads(ud.layout_json)
    if template:
        return json.loads(template.layout_json)
    return SUPERADMIN_LAYOUT if is_superadmin else DEFAULT_LAYOUT


def _template_out(t: DashboardTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "business_id": t.business_id,
        "layout": json.loads(t.layout_json),
        "is_default": t.is_default,
        "created_at": str(t.created_at) if t.created_at else None,
    }


def _widget_out(w: WidgetDefinition) -> dict:
    return {
        "id": w.id,
        "type": w.type,
        "title": w.title,
        "description": w.description,
        "icon": w.icon,
        "default_config": json.loads(w.default_config_json or "{}"),
        "is_system": w.is_system,
        "business_id": w.business_id,
        "created_at": str(w.created_at) if w.created_at else None,
    }


# ── Worker: get/save own dashboard ───────────────────────────────────────────

@worker_router.get("/me/dashboard/{business_id}")
def get_my_dashboard(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    ud = db.execute(
        select(UserDashboard).where(
            UserDashboard.user_id == user.id,
            UserDashboard.business_id == business_id,
        )
    ).scalar_one_or_none()

    template = None
    if ud and ud.template_id:
        template = db.get(DashboardTemplate, ud.template_id)
    elif not ud:
        # Try default template for business
        template = db.execute(
            select(DashboardTemplate).where(
                DashboardTemplate.business_id == business_id,
                DashboardTemplate.is_default.is_(True),
            )
        ).scalar_one_or_none()
        if not template:
            # Global default
            template = db.execute(
                select(DashboardTemplate).where(
                    DashboardTemplate.business_id.is_(None),
                    DashboardTemplate.is_default.is_(True),
                )
            ).scalar_one_or_none()

    layout = _effective_layout(ud, template, user.is_superadmin)
    return {
        "layout": layout,
        "is_locked": ud.is_locked if ud else False,
        "template_id": ud.template_id if ud else (template.id if template else None),
        "can_customize": not (ud.is_locked if ud else False),
    }


class SaveLayoutRequest(BaseModel):
    layout: list


@worker_router.patch("/me/dashboard/{business_id}")
def save_my_dashboard(
    business_id: str,
    payload: SaveLayoutRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    ud = db.execute(
        select(UserDashboard).where(
            UserDashboard.user_id == user.id,
            UserDashboard.business_id == business_id,
        )
    ).scalar_one_or_none()
    if ud and ud.is_locked:
        raise HTTPException(403, "Dashboard is locked by an administrator")
    if not ud:
        ud = UserDashboard(user_id=user.id, business_id=business_id)
        db.add(ud)
    ud.layout_json = json.dumps(payload.layout)
    db.commit()
    return {"ok": True, "slots": len(payload.layout)}


# ── Tenant: templates ─────────────────────────────────────────────────────────

@tenant_router.get("/dashboard/templates", dependencies=[require_permission("schedule:read")])
def list_templates(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    rows = db.execute(
        select(DashboardTemplate).where(
            (DashboardTemplate.business_id == business_id) |
            (DashboardTemplate.business_id.is_(None))
        ).order_by(DashboardTemplate.is_default.desc(), DashboardTemplate.name)
    ).scalars().all()
    return [_template_out(t) for t in rows]


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    layout: list
    is_default: bool = False


@tenant_router.post("/dashboard/templates", status_code=201, dependencies=[require_permission("schedule:write")])
def create_template(
    business_id: str,
    payload: TemplateCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if payload.is_default:
        # Unset other defaults for this business
        db.execute(
            select(DashboardTemplate).where(
                DashboardTemplate.business_id == business_id,
                DashboardTemplate.is_default.is_(True),
            )
        )
        for t in db.execute(select(DashboardTemplate).where(
            DashboardTemplate.business_id == business_id,
            DashboardTemplate.is_default.is_(True),
        )).scalars().all():
            t.is_default = False

    t = DashboardTemplate(
        business_id=business_id,
        created_by=user.id,
        name=payload.name,
        description=payload.description,
        layout_json=json.dumps(payload.layout),
        is_default=payload.is_default,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _template_out(t)


@tenant_router.patch("/dashboard/templates/{template_id}", dependencies=[require_permission("schedule:write")])
def update_template(
    business_id: str,
    template_id: str,
    payload: TemplateCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    t = db.get(DashboardTemplate, template_id)
    if not t or (t.business_id != business_id and t.business_id is not None):
        raise HTTPException(404, "Template not found")
    t.name = payload.name
    t.description = payload.description
    t.layout_json = json.dumps(payload.layout)
    if payload.is_default and not t.is_default:
        for other in db.execute(select(DashboardTemplate).where(
            DashboardTemplate.business_id == business_id, DashboardTemplate.is_default.is_(True),
        )).scalars().all():
            other.is_default = False
    t.is_default = payload.is_default
    db.commit()
    return _template_out(t)


@tenant_router.delete("/dashboard/templates/{template_id}", status_code=204,
                      dependencies=[require_permission("schedule:write")])
def delete_template(
    business_id: str,
    template_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    t = db.get(DashboardTemplate, template_id)
    if not t or (t.business_id not in [business_id, None]):
        raise HTTPException(404, "Template not found")
    if t.business_id is None:
        raise HTTPException(403, "Cannot delete global templates")
    db.delete(t)
    db.commit()


class AssignDashboardRequest(BaseModel):
    membership_id: str
    template_id: Optional[str] = None
    is_locked: bool = False
    reset_layout: bool = False


@tenant_router.post("/dashboard/assign", dependencies=[require_permission("schedule:write")])
def assign_dashboard(
    business_id: str,
    payload: AssignDashboardRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    m = db.get(Membership, payload.membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    ud = db.execute(
        select(UserDashboard).where(
            UserDashboard.user_id == m.user_id,
            UserDashboard.business_id == business_id,
        )
    ).scalar_one_or_none()
    if not ud:
        ud = UserDashboard(user_id=m.user_id, business_id=business_id)
        db.add(ud)
    ud.template_id = payload.template_id
    ud.is_locked = payload.is_locked
    if payload.reset_layout:
        ud.layout_json = None
    db.commit()
    return {"ok": True, "user_id": m.user_id, "is_locked": ud.is_locked}


@tenant_router.get("/dashboard/members", dependencies=[require_permission("members:read")])
def list_member_dashboards(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    """List all members with their dashboard config for this business."""
    memberships = db.execute(
        select(Membership).where(
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()
    result = []
    for m in memberships:
        u = db.get(User, m.user_id)
        ud = db.execute(
            select(UserDashboard).where(
                UserDashboard.user_id == m.user_id,
                UserDashboard.business_id == business_id,
            )
        ).scalar_one_or_none()
        result.append({
            "membership_id": m.id,
            "user_id": m.user_id,
            "email": u.email if u else None,
            "template_id": ud.template_id if ud else None,
            "is_locked": ud.is_locked if ud else False,
            "has_custom_layout": bool(ud and ud.layout_json),
        })
    return result


# ── Control: Widget Definitions ───────────────────────────────────────────────

@control_router.get("/widgets")
def list_widgets(
    user: SuperAdmin,
    db: Session = Depends(get_db),
    business_id: Optional[str] = None,
):
    q = select(WidgetDefinition)
    if business_id:
        q = q.where(
            (WidgetDefinition.business_id == business_id) |
            (WidgetDefinition.business_id.is_(None))
        )
    rows = db.execute(q.order_by(WidgetDefinition.is_system.desc(), WidgetDefinition.title)).scalars().all()
    return [_widget_out(w) for w in rows]


class WidgetCreate(BaseModel):
    type: str
    title: str
    description: Optional[str] = None
    icon: str = "bi-grid"
    default_config: dict = {}
    business_id: Optional[str] = None


@control_router.post("/widgets", status_code=201)
def create_widget(payload: WidgetCreate, user: SuperAdmin, db: Session = Depends(get_db)):
    w = WidgetDefinition(
        type=payload.type,
        title=payload.title,
        description=payload.description,
        icon=payload.icon,
        default_config_json=json.dumps(payload.default_config),
        is_system=False,
        business_id=payload.business_id,
        created_by=user.id,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return _widget_out(w)


@control_router.patch("/widgets/{widget_id}")
def update_widget(widget_id: str, payload: WidgetCreate, user: SuperAdmin, db: Session = Depends(get_db)):
    w = db.get(WidgetDefinition, widget_id)
    if not w:
        raise HTTPException(404, "Widget not found")
    if w.is_system:
        raise HTTPException(403, "Cannot modify system widgets")
    w.type = payload.type
    w.title = payload.title
    w.description = payload.description
    w.icon = payload.icon
    w.default_config_json = json.dumps(payload.default_config)
    db.commit()
    return _widget_out(w)


@control_router.delete("/widgets/{widget_id}", status_code=204)
def delete_widget(widget_id: str, user: SuperAdmin, db: Session = Depends(get_db)):
    w = db.get(WidgetDefinition, widget_id)
    if not w:
        raise HTTPException(404, "Widget not found")
    if w.is_system:
        raise HTTPException(403, "Cannot delete system widgets")
    db.delete(w)
    db.commit()


# ── Control: Permissions Manager ─────────────────────────────────────────────

@control_router.get("/permissions-manager")
def permissions_manager(user: SuperAdmin, db: Session = Depends(get_db)):
    """Return all businesses with their roles and current permission assignments."""
    from apps.api.app.models.business import Business
    businesses = db.execute(select(Business).where(Business.deleted_at == None)).scalars().all()  # noqa: E711
    all_perms = db.execute(select(Permission).order_by(Permission.key)).scalars().all()
    result = []
    for biz in businesses:
        roles = db.execute(select(BizRole).where(BizRole.business_id == biz.id)).scalars().all()
        roles_out = []
        for role in roles:
            assigned = db.execute(
                select(Permission.key).join(
                    BizRolePermission, BizRolePermission.permission_id == Permission.id
                ).where(BizRolePermission.role_id == role.id)
            ).scalars().all()
            roles_out.append({
                "id": role.id,
                "name": role.name,
                "is_system_template": role.is_system_template,
                "permissions": list(assigned),
            })
        result.append({
            "id": biz.id,
            "name": biz.name,
            "plan": biz.plan,
            "roles": roles_out,
        })
    return {
        "businesses": result,
        "all_permissions": [{"id": p.id, "key": p.key, "description": p.description} for p in all_perms],
    }


class PermBulkUpdate(BaseModel):
    role_id: str
    permissions: list  # list of permission keys to SET (replaces all)


@control_router.post("/permissions-manager/role-perms")
def set_role_permissions(payload: PermBulkUpdate, user: SuperAdmin, db: Session = Depends(get_db)):
    role = db.get(BizRole, payload.role_id)
    if not role:
        raise HTTPException(404, "Role not found")
    # Remove all existing
    existing = db.execute(
        select(BizRolePermission).where(BizRolePermission.role_id == role.id)
    ).scalars().all()
    for e in existing:
        db.delete(e)
    # Add requested
    added = []
    for key in payload.permissions:
        perm = db.execute(select(Permission).where(Permission.key == key)).scalar_one_or_none()
        if not perm:
            perm = Permission(key=key, description=key)
            db.add(perm)
            db.flush()
        db.add(BizRolePermission(role_id=role.id, permission_id=perm.id))
        added.append(key)
    db.commit()
    return {"role_id": role.id, "permissions": added}


@control_router.post("/permissions-manager/add-perm")
def add_global_permission(user: SuperAdmin, db: Session = Depends(get_db), key: str = "", description: str = ""):
    existing = db.execute(select(Permission).where(Permission.key == key)).scalar_one_or_none()
    if existing:
        raise HTTPException(409, f"Permission '{key}' already exists")
    p = Permission(key=key, description=description)
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "key": p.key, "description": p.description}
