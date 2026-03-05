"""
FastAPI dependency functions for authentication and authorization.

Provides:
  - get_current_user        – JWT bearer auth → User
  - get_current_superadmin  – must be superadmin
  - get_agent_from_key      – API key auth → Agent
  - require_permission(key) – returns a dependency that checks RBAC
  - get_tenant_ctx          – returns TenantContext for the current user+business
"""
import json
from dataclasses import dataclass, field
from datetime import timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Path, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_access_token, hash_api_key
from app.models.identity import (
    Agent, AgentCredential, AgentStatus,
    BizRole, BizRolePermission, Membership, MembershipLocationRole, MembershipRole,
    MembershipStatus, Permission, User, UserStatus,
)


@dataclass
class TenantContext:
    """Resolved tenant context for a request: user + business + permissions."""
    user_id: str
    business_id: str
    is_superadmin: bool
    permissions: set[str] = field(default_factory=set)
    location_ids: list[str] = field(default_factory=list)  # optional location scope

    def has_permission(self, key: str) -> bool:
        return "*" in self.permissions or key in self.permissions

bearer_scheme = HTTPBearer(auto_error=False)

CredDep = Annotated[HTTPAuthorizationCredentials | None, Security(bearer_scheme)]
DBDep = Annotated[Session, Depends(get_db)]


# ── JWT auth ─────────────────────────────────────────────────────────────────

def get_current_user(
    creds: CredDep,
    db: DBDep,
) -> User:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    try:
        payload = decode_access_token(creds.credentials)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not an access token")

    user = db.get(User, payload["sub"])
    if not user or user.status != UserStatus.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_superadmin(user: CurrentUser) -> User:
    if not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Superadmin access required")
    return user


SuperAdmin = Annotated[User, Depends(get_current_superadmin)]


# ── Agent / API key auth ──────────────────────────────────────────────────────

def get_agent_from_key(
    creds: CredDep,
    db: DBDep,
) -> Agent:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key")
    key_hash = hash_api_key(creds.credentials)
    cred = db.execute(
        select(AgentCredential).where(
            AgentCredential.key_hash == key_hash,
            AgentCredential.revoked == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    if not cred:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked API key")
    # Check expiry
    if cred.expires_at:
        exp = cred.expires_at
        if isinstance(exp, str):
            from datetime import datetime
            exp = datetime.fromisoformat(exp)
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key expired")
    agent = db.get(Agent, cred.agent_id)
    if not agent or agent.status != AgentStatus.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Agent inactive or not found")
    # Attach scopes to agent for downstream use
    agent._scopes = json.loads(cred.scopes_json)  # type: ignore[attr-defined]
    return agent


CurrentAgent = Annotated[Agent, Depends(get_agent_from_key)]


# ── Tenant resolution ─────────────────────────────────────────────────────────

def _resolve_business_id(
    user: User,
    business_id: str,
    db: Session,
) -> str:
    """Verify the user has an active membership in this business."""
    if user.is_superadmin:
        return business_id  # superadmins can access any tenant
    membership = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalar_one_or_none()
    if not membership:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No active membership in this business")
    return business_id


# ── RBAC ──────────────────────────────────────────────────────────────────────

def _get_user_permissions(user: User, business_id: str, db: Session) -> set[str]:
    """Return the set of permission keys the user holds in a business.
    Effective permissions = business-level role perms ∪ all location-level role perms.
    """
    if user.is_superadmin:
        return {"*"}  # superadmins have all permissions

    # Business-level permissions (via MembershipRole)
    biz_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipRole, MembershipRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()

    # Location-level permissions (via MembershipLocationRole — additive)
    loc_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipLocationRole, MembershipLocationRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipLocationRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()

    return set(biz_perms) | set(loc_perms)


def _get_user_location_permissions(user: User, business_id: str, location_id: str, db: Session) -> set[str]:
    """Permissions at a specific location: business-wide role perms + location-scoped role perms for that location only."""
    if user.is_superadmin:
        return {"*"}

    biz_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipRole, MembershipRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()

    loc_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipLocationRole, MembershipLocationRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipLocationRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
            MembershipLocationRole.location_id == location_id,
        )
    ).scalars().all()

    return set(biz_perms) | set(loc_perms)


def require_permission(permission_key: str):
    """
    Dependency factory. Usage:

        @router.get("/foo")
        def foo(
            user: CurrentUser,
            _: None = Depends(require_permission("schedule:read")),
            business_id: str = Path(...),
            location_id: str | None = Path(None),  # optional location scope
            db: Session = Depends(get_db),
        ):
    
    Behavior: if a location_id path parameter is present and not None, the
    dependency will validate the permission in the context of that location
    (business-wide permissions still apply). Otherwise it validates business-wide perms.
    """
    def _dep(
        user: CurrentUser,
        business_id: str,
        db: DBDep,
        location_id: str | None = None,
    ) -> None:
        # Ensure the user is a member of the business (superadmins bypass)
        _resolve_business_id(user, business_id, db)

        # If a location_id is supplied, check location-scoped permissions first
        if location_id:
            perms = _get_user_location_permissions(user, business_id, location_id, db)
        else:
            perms = _get_user_permissions(user, business_id, db)

        if "*" not in perms and permission_key not in perms:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Missing permission: {permission_key}",
            )

    return Depends(_dep)


def require_membership():
    """Dependency: requires only an active membership (no specific permission)."""
    def _dep(
        user: CurrentUser,
        business_id: Annotated[str, Path()],
        db: DBDep,
    ) -> None:
        _resolve_business_id(user, business_id, db)

    return Depends(_dep)


def has_location_permission(user: User, business_id: str, location_id: str, permission_key: str, db: Session) -> bool:
    """Imperative check: does user have permission_key at a specific location?"""
    perms = _get_user_location_permissions(user, business_id, location_id, db)
    return "*" in perms or permission_key in perms


def agent_require_scope(scope: str):
    """Dependency factory for agent scope checking."""
    def _dep(agent: CurrentAgent) -> None:
        scopes = getattr(agent, "_scopes", [])
        if "*" not in scopes and scope not in scopes:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Agent missing scope: {scope}",
            )
    return Depends(_dep)


def get_tenant_ctx(
    user: CurrentUser,
    business_id: Annotated[str, Path()],
    db: DBDep,
) -> TenantContext:
    """
    Dependency that resolves and returns a TenantContext for the current
    user + business_id path parameter.  Raises 403 if user has no active
    membership (superadmins bypass the membership check).
    """
    _resolve_business_id(user, business_id, db)
    perms = _get_user_permissions(user, business_id, db)

    # Collect location IDs the user is assigned to
    from app.models.identity import MembershipLocationRole as MLR
    loc_rows = db.execute(
        select(MLR.location_id)
        .join(Membership, Membership.id == MLR.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()

    return TenantContext(
        user_id=user.id,
        business_id=business_id,
        is_superadmin=user.is_superadmin,
        permissions=perms,
        location_ids=list(set(loc_rows)),
    )


TenantCtx = Annotated[TenantContext, Depends(get_tenant_ctx)]
