"""
Messaging API — ephemeral walkie-talkie style channels.

Planes
------
worker_router  : /api/v1/messaging/            (JWT auth)
tenant_router  : /api/v1/tenant/{biz}/messaging/ (JWT + manage perm)
external_router: /api/v1/external/messaging/   (API key auth)
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, DBDep, _get_user_permissions, require_permission
from apps.api.app.core.db import get_db
from apps.api.app.models.identity import Membership, MembershipStatus, User
from apps.api.app.models.messaging import (
    Channel, ChannelMember, ChannelType, MemberRole, Message,
    MessageSource, MessagingApiKey,
)

if TYPE_CHECKING:
    pass

# ── In-memory WebSocket registry ──────────────────────────────────────────────
# channel_id → set of live WebSocket connections
_ws_connections: dict[str, set[WebSocket]] = {}

TTL_HOURS = 48


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expires() -> datetime:
    return _now() + timedelta(hours=TTL_HOURS)


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChannelCreate(BaseModel):
    name: str
    type: ChannelType = ChannelType.group
    description: str | None = None
    member_user_ids: list[str] = []
    business_id: str | None = None  # required for superadmins / multi-biz users


class MessageCreate(BaseModel):
    content: str


class BroadcastCreate(BaseModel):
    content: str
    business_id: str | None = None  # required for superadmins / multi-biz users


class ApiKeyCreate(BaseModel):
    name: str
    permissions: list[str] = ["read", "write"]  # "read" and/or "write"
    channel_ids: list[str] = []                  # empty = all channels in biz


class AddMemberBody(BaseModel):
    user_id: str
    role: MemberRole = MemberRole.member


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_channel_or_404(channel_id: str, db: Session) -> Channel:
    ch = db.get(Channel, channel_id)
    if not ch or ch.is_archived:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Channel not found")
    return ch


def _assert_member(user_id: str, channel: Channel) -> ChannelMember:
    for m in channel.members:
        if m.user_id == user_id:
            return m
    raise HTTPException(status.HTTP_403_FORBIDDEN, "Not a member of this channel")


def _assert_biz_perm(user: User, business_id: str, perm: str, db: Session) -> None:
    if user.is_superadmin:
        return
    perms = _get_user_permissions(user, business_id, db)
    if "*" not in perms and perm not in perms:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Missing permission: {perm}")


def _display_name(user: User) -> str:
    parts = [user.first_name, user.last_name]
    name = " ".join(p for p in parts if p)
    return name if name else user.email


def _serialize_channel(ch: Channel, user_id: str, db: Session) -> dict:
    recent = db.execute(
        select(Message)
        .where(Message.channel_id == ch.id, Message.expires_at > _now())
        .order_by(Message.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return {
        "id": ch.id,
        "business_id": ch.business_id,
        "name": ch.name,
        "type": ch.type,
        "description": ch.description,
        "member_count": len(ch.members),
        "last_message": _serialize_message(recent) if recent else None,
    }


def _serialize_message(msg: Message) -> dict:
    return {
        "id": msg.id,
        "channel_id": msg.channel_id,
        "sender_id": msg.sender_id,
        "sender_name": msg.sender_name,
        "content": msg.content,
        "source": msg.source,
        "created_at": msg.created_at.isoformat(),
        "expires_at": msg.expires_at.isoformat(),
    }


async def _broadcast_ws(channel_id: str, payload: dict) -> None:
    """Push a message dict to all WebSocket subscribers of a channel."""
    dead = set()
    for ws in _ws_connections.get(channel_id, set()):
        try:
            await ws.send_json(payload)
        except Exception:
            dead.add(ws)
    if dead:
        _ws_connections[channel_id] -= dead


def _get_api_key_or_401(raw_key: str, db: Session) -> MessagingApiKey:
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    ak = db.execute(
        select(MessagingApiKey).where(
            MessagingApiKey.key_hash == key_hash,
            MessagingApiKey.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if not ak:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    return ak


def _purge_expired(db: Session) -> None:
    """Delete messages past their TTL."""
    db.execute(
        Message.__table__.delete().where(Message.expires_at <= _now())
    )
    db.commit()


# ── Worker router ─────────────────────────────────────────────────────────────
worker_router = APIRouter(prefix="/api/v1/messaging", tags=["messaging-worker"])


@worker_router.get("/channels")
def list_my_channels(user: CurrentUser, db: DBDep):
    """List all channels the current user is a member of."""
    memberships = db.execute(
        select(ChannelMember).where(ChannelMember.user_id == user.id)
    ).scalars().all()
    channel_ids = [m.channel_id for m in memberships]
    channels = db.execute(
        select(Channel).where(Channel.id.in_(channel_ids), Channel.is_archived.is_(False))
    ).scalars().all()
    return [_serialize_channel(ch, user.id, db) for ch in channels]


@worker_router.post("/channels", status_code=201)
def create_channel(body: ChannelCreate, user: CurrentUser, db: DBDep):
    """Create a new group or direct channel (messaging:manage required for announcement type)."""
    # Use explicit business_id from body, or derive from creator's first active membership
    if body.business_id:
        biz_id = body.business_id
        if not user.is_superadmin:
            _assert_biz_perm(user, biz_id, "messaging:write", db)
    else:
        creator_memberships = db.execute(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.status == MembershipStatus.active,
            )
        ).scalars().all()
        if not creator_memberships:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No active business membership")
        biz_id = creator_memberships[0].business_id

    if body.type == ChannelType.announcement:
        _assert_biz_perm(user, biz_id, "messaging:manage", db)

    ch = Channel(
        business_id=biz_id,
        name=body.name,
        type=body.type,
        description=body.description,
        created_by=user.id,
    )
    db.add(ch)
    db.flush()

    # Add creator as admin
    db.add(ChannelMember(channel_id=ch.id, user_id=user.id, role=MemberRole.admin, joined_at=_now()))

    # Add other members
    for uid in body.member_user_ids:
        if uid != user.id:
            db.add(ChannelMember(channel_id=ch.id, user_id=uid, role=MemberRole.member, joined_at=_now()))

    db.commit()
    db.refresh(ch)
    return _serialize_channel(ch, user.id, db)


@worker_router.post("/channels/{channel_id}/members", status_code=201)
def add_member(channel_id: str, body: AddMemberBody, user: CurrentUser, db: DBDep):
    ch = _get_channel_or_404(channel_id, db)
    me = _assert_member(user.id, ch)
    if me.role != MemberRole.admin and not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Channel admin required")
    existing = db.execute(
        select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == body.user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return {"detail": "Already a member"}
    db.add(ChannelMember(channel_id=channel_id, user_id=body.user_id, role=body.role, joined_at=_now()))
    db.commit()
    return {"detail": "Added"}


@worker_router.delete("/channels/{channel_id}/members/{user_id}", status_code=204)
def remove_member(channel_id: str, user_id: str, user: CurrentUser, db: DBDep):
    ch = _get_channel_or_404(channel_id, db)
    me = _assert_member(user.id, ch)
    if me.role != MemberRole.admin and user.id != user_id and not user.is_superadmin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Channel admin required")
    target = db.execute(
        select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if target:
        db.delete(target)
        db.commit()


@worker_router.get("/channels/{channel_id}/messages")
def get_messages(channel_id: str, user: CurrentUser, db: DBDep, limit: int = 50):
    """Fetch recent non-expired messages for a channel."""
    ch = _get_channel_or_404(channel_id, db)
    _assert_member(user.id, ch)
    _purge_expired(db)
    msgs = db.execute(
        select(Message)
        .where(Message.channel_id == channel_id, Message.expires_at > _now())
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [_serialize_message(m) for m in reversed(msgs)]


@worker_router.post("/channels/{channel_id}/messages", status_code=201)
async def send_message(channel_id: str, body: MessageCreate, user: CurrentUser, db: DBDep):
    """Send a message to a channel."""
    ch = _get_channel_or_404(channel_id, db)
    _assert_member(user.id, ch)
    biz_id = ch.business_id

    if ch.type == ChannelType.announcement:
        _assert_biz_perm(user, biz_id, "messaging:broadcast", db)
    else:
        _assert_biz_perm(user, biz_id, "messaging:write", db)

    msg = Message(
        channel_id=channel_id,
        sender_id=user.id,
        sender_name=_display_name(user),
        content=body.content,
        source=MessageSource.user,
        created_at=_now(),
        expires_at=_expires(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    payload = _serialize_message(msg)
    await _broadcast_ws(channel_id, {"event": "message", "data": payload})
    return payload


@worker_router.delete("/channels/{channel_id}/messages/{message_id}", status_code=204)
def delete_message(channel_id: str, message_id: str, user: CurrentUser, db: DBDep):
    ch = _get_channel_or_404(channel_id, db)
    _assert_member(user.id, ch)
    msg = db.get(Message, message_id)
    if not msg or msg.channel_id != channel_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    if msg.sender_id != user.id and not user.is_superadmin:
        _assert_biz_perm(user, ch.business_id, "messaging:manage", db)
    db.delete(msg)
    db.commit()


@worker_router.get("/unread")
def get_unread(user: CurrentUser, db: DBDep):
    """Return total unread message count across all user's channels (simple: latest 48h count per channel)."""
    memberships = db.execute(
        select(ChannelMember).where(ChannelMember.user_id == user.id)
    ).scalars().all()
    result = {}
    _purge_expired(db)
    for m in memberships:
        count = db.execute(
            select(Message)
            .where(Message.channel_id == m.channel_id, Message.expires_at > _now())
        ).scalars()
        result[m.channel_id] = len(list(count))
    return result


@worker_router.post("/broadcast", status_code=201)
async def broadcast_all(body: BroadcastCreate, user: CurrentUser, db: DBDep):
    """Post an announcement to all announcement channels in the user's business."""
    if body.business_id:
        biz_id = body.business_id
    else:
        memberships = db.execute(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.status == MembershipStatus.active,
            )
        ).scalars().all()
        if not memberships:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No active membership")
        biz_id = memberships[0].business_id
    _assert_biz_perm(user, biz_id, "messaging:broadcast", db)

    channels = db.execute(
        select(Channel).where(
            Channel.business_id == biz_id,
            Channel.type == ChannelType.announcement,
            Channel.is_archived.is_(False),
        )
    ).scalars().all()

    sent = []
    for ch in channels:
        msg = Message(
            channel_id=ch.id,
            sender_id=user.id,
            sender_name=_display_name(user),
            content=body.content,
            source=MessageSource.user,
            created_at=_now(),
            expires_at=_expires(),
        )
        db.add(msg)
        db.flush()
        db.refresh(msg)
        payload = _serialize_message(msg)
        await _broadcast_ws(ch.id, {"event": "message", "data": payload})
        sent.append(payload)

    db.commit()
    return {"broadcast_count": len(sent), "messages": sent}


@worker_router.post("/dm/{target_user_id}", status_code=201)
async def send_dm(target_user_id: str, body: MessageCreate, user: CurrentUser, db: DBDep):
    """Find or create a DM channel between current user and target, then send."""
    if target_user_id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot DM yourself")

    # Determine shared business
    my_biz_ids = {m.business_id for m in db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()}
    their_biz_ids = {m.business_id for m in db.execute(
        select(Membership).where(
            Membership.user_id == target_user_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()}
    shared = my_biz_ids & their_biz_ids
    if not shared:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "No shared business with target user")
    biz_id = next(iter(shared))
    _assert_biz_perm(user, biz_id, "messaging:write", db)

    # Find existing DM channel between these two users
    existing_dm = None
    my_dm_channel_ids = {m.channel_id for m in db.execute(
        select(ChannelMember).where(ChannelMember.user_id == user.id)
    ).scalars().all()}
    their_dm_channel_ids = {m.channel_id for m in db.execute(
        select(ChannelMember).where(ChannelMember.user_id == target_user_id)
    ).scalars().all()}
    shared_channels = my_dm_channel_ids & their_dm_channel_ids
    if shared_channels:
        candidate = db.execute(
            select(Channel).where(
                Channel.id.in_(shared_channels),
                Channel.type == ChannelType.direct,
                Channel.business_id == biz_id,
                Channel.is_archived.is_(False),
            )
        ).scalar_one_or_none()
        existing_dm = candidate

    if not existing_dm:
        target = db.get(User, target_user_id)
        target_name = target.email if target else target_user_id[:8]
        existing_dm = Channel(
            business_id=biz_id,
            name=f"DM: {user.email} ↔ {target_name}",
            type=ChannelType.direct,
            created_by=user.id,
        )
        db.add(existing_dm)
        db.flush()
        db.add(ChannelMember(channel_id=existing_dm.id, user_id=user.id, role=MemberRole.member, joined_at=_now()))
        db.add(ChannelMember(channel_id=existing_dm.id, user_id=target_user_id, role=MemberRole.member, joined_at=_now()))
        db.flush()

    msg = Message(
        channel_id=existing_dm.id,
        sender_id=user.id,
        sender_name=_display_name(user),
        content=body.content,
        source=MessageSource.user,
        created_at=_now(),
        expires_at=_expires(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    db.refresh(existing_dm)

    payload = _serialize_message(msg)
    await _broadcast_ws(existing_dm.id, {"event": "message", "data": payload})
    return {"channel": _serialize_channel(existing_dm, user.id, db), "message": payload}


@worker_router.websocket("/ws/{channel_id}")
async def ws_channel(channel_id: str, websocket: WebSocket, token: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time message streaming.
    Connect with: ws://host/api/v1/messaging/ws/{channel_id}?token=<jwt>
    Requires ASGI server (uvicorn). On WSGI deployments use polling instead.
    """
    from apps.api.app.core.security import decode_access_token

    await websocket.accept()

    # Auth via query param token
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        user = db.get(User, user_id)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    ch = db.get(Channel, channel_id)
    if not ch:
        await websocket.close(code=4004, reason="Channel not found")
        return

    is_member = any(m.user_id == user_id for m in ch.members)
    if not is_member:
        await websocket.close(code=4003, reason="Not a member")
        return

    # Register
    _ws_connections.setdefault(channel_id, set()).add(websocket)
    try:
        while True:
            # Keep connection alive; client sends pings as needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_connections.get(channel_id, set()).discard(websocket)


# ── Tenant router (channel + API key management) ──────────────────────────────
tenant_router = APIRouter(prefix="/api/v1/tenant/{business_id}/messaging", tags=["messaging-tenant"])


@tenant_router.get("/channels")
def tenant_list_channels(
    business_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    """List all channels for a business (manager view)."""
    channels = db.execute(
        select(Channel).where(
            Channel.business_id == business_id,
            Channel.is_archived.is_(False),
            Channel.type != ChannelType.direct,
        )
    ).scalars().all()
    return [_serialize_channel(ch, user.id, db) for ch in channels]


@tenant_router.post("/channels", status_code=201)
def tenant_create_channel(
    business_id: Annotated[str, Path()],
    body: ChannelCreate,
    user: CurrentUser,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    ch = Channel(
        business_id=business_id,
        name=body.name,
        type=body.type,
        description=body.description,
        created_by=user.id,
    )
    db.add(ch)
    db.flush()
    db.add(ChannelMember(channel_id=ch.id, user_id=user.id, role=MemberRole.admin, joined_at=_now()))
    for uid in body.member_user_ids:
        if uid != user.id:
            db.add(ChannelMember(channel_id=ch.id, user_id=uid, role=MemberRole.member, joined_at=_now()))
    db.commit()
    db.refresh(ch)
    return _serialize_channel(ch, user.id, db)


@tenant_router.delete("/channels/{channel_id}", status_code=204)
def tenant_delete_channel(
    business_id: Annotated[str, Path()],
    channel_id: str,
    user: CurrentUser,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    ch = _get_channel_or_404(channel_id, db)
    if ch.business_id != business_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Channel not found")
    ch.is_archived = True
    db.commit()


@tenant_router.post("/channels/{channel_id}/members/{user_id}", status_code=201)
def tenant_add_member(
    business_id: Annotated[str, Path()],
    channel_id: str,
    user_id: str,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    ch = _get_channel_or_404(channel_id, db)
    if ch.business_id != business_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Channel not found")
    existing = db.execute(
        select(ChannelMember).where(
            ChannelMember.channel_id == channel_id,
            ChannelMember.user_id == user_id,
        )
    ).scalar_one_or_none()
    if existing:
        return {"detail": "Already a member"}
    db.add(ChannelMember(channel_id=channel_id, user_id=user_id, role=MemberRole.member, joined_at=_now()))
    db.commit()
    return {"detail": "Added"}


# ── API Key management ─────────────────────────────────────────────────────────

@tenant_router.get("/api-keys")
def list_api_keys(
    business_id: Annotated[str, Path()],
    user: CurrentUser,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    keys = db.execute(
        select(MessagingApiKey).where(MessagingApiKey.business_id == business_id)
    ).scalars().all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "permissions": k.permissions,
            "channel_ids": k.channel_ids,
            "is_active": k.is_active,
            "created_at": k.created_at.isoformat(),
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
        }
        for k in keys
    ]


@tenant_router.post("/api-keys", status_code=201)
def create_api_key(
    business_id: Annotated[str, Path()],
    body: ApiKeyCreate,
    user: CurrentUser,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    raw_key = secrets.token_hex(32)  # 64-char hex key shown once
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    ak = MessagingApiKey(
        business_id=business_id,
        name=body.name,
        key_hash=key_hash,
        permissions=body.permissions,
        channel_ids=body.channel_ids,
        created_by=user.id,
    )
    db.add(ak)
    db.commit()
    db.refresh(ak)
    return {
        "id": ak.id,
        "name": ak.name,
        "key": raw_key,  # shown only once
        "permissions": ak.permissions,
        "channel_ids": ak.channel_ids,
    }


@tenant_router.delete("/api-keys/{key_id}", status_code=204)
def revoke_api_key(
    business_id: Annotated[str, Path()],
    key_id: str,
    db: DBDep,
    _: None = require_permission("messaging:manage"),
):
    ak = db.get(MessagingApiKey, key_id)
    if not ak or ak.business_id != business_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found")
    ak.is_active = False
    db.commit()


# ── External (3rd-party API key) router ───────────────────────────────────────
external_router = APIRouter(prefix="/api/v1/external/messaging", tags=["messaging-external"])


class ExternalMessageCreate(BaseModel):
    content: str
    sender_name: str = "External App"


@external_router.post("/channels/{channel_id}/messages", status_code=201)
async def external_post_message(
    channel_id: str,
    body: ExternalMessageCreate,
    db: DBDep,
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
):
    """Post a message to a channel using a named API key (X-Api-Key header)."""
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-Api-Key required")

    ak = _get_api_key_or_401(x_api_key, db)

    ch = _get_channel_or_404(channel_id, db)
    if ch.business_id != ak.business_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Key not valid for this business")

    if ak.channel_ids and channel_id not in ak.channel_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Key not permitted for this channel")

    if "write" not in ak.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Key lacks write permission")

    # Update last_used_at
    ak.last_used_at = _now()

    msg = Message(
        channel_id=channel_id,
        sender_id=ak.id,
        sender_name=body.sender_name,
        content=body.content,
        source=MessageSource.api_key,
        api_key_id=ak.id,
        created_at=_now(),
        expires_at=_expires(),
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    payload = _serialize_message(msg)
    await _broadcast_ws(channel_id, {"event": "message", "data": payload})
    return payload


@external_router.get("/channels/{channel_id}/messages")
def external_get_messages(
    channel_id: str,
    db: DBDep,
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    limit: int = 50,
):
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-Api-Key required")

    ak = _get_api_key_or_401(x_api_key, db)
    ch = _get_channel_or_404(channel_id, db)
    if ch.business_id != ak.business_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Key not valid for this business")
    if ak.channel_ids and channel_id not in ak.channel_ids:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Key not permitted for this channel")
    if "read" not in ak.permissions:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Key lacks read permission")

    ak.last_used_at = _now()
    db.commit()

    _purge_expired(db)
    msgs = db.execute(
        select(Message)
        .where(Message.channel_id == channel_id, Message.expires_at > _now())
        .order_by(Message.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [_serialize_message(m) for m in reversed(msgs)]
