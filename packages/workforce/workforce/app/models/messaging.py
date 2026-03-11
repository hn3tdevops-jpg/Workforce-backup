"""
Messaging models — ephemeral walkie-talkie style communication.
Messages expire after 48 hours (enforced by expires_at + background cleanup).
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base, TimestampMixin, UUIDMixin


class ChannelType(str, enum.Enum):
    announcement = "announcement"  # manager-only posts; workers read-only
    group        = "group"         # any member can post
    direct       = "direct"        # exactly 2 members, 1:1


class MemberRole(str, enum.Enum):
    admin  = "admin"   # can manage channel membership
    member = "member"


class MessageSource(str, enum.Enum):
    user    = "user"    # posted by an authenticated user
    api_key = "api_key" # posted by an external API key


class Channel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "msg_channels"

    business_id: Mapped[str]      = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name:        Mapped[str]      = mapped_column(String(100), nullable=False)
    type:        Mapped[ChannelType] = mapped_column(Enum(ChannelType, name="channel_type"), nullable=False, default=ChannelType.group)
    description: Mapped[str|None] = mapped_column(Text, nullable=True)
    created_by:  Mapped[str|None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_archived: Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)

    members:  Mapped[list["ChannelMember"]] = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")
    messages: Mapped[list["Message"]]       = relationship("Message", back_populates="channel", cascade="all, delete-orphan")


class ChannelMember(Base):
    __tablename__ = "msg_channel_members"
    __table_args__ = (UniqueConstraint("channel_id", "user_id", name="uq_channel_member"),)

    channel_id: Mapped[str]        = mapped_column(String(36), ForeignKey("msg_channels.id", ondelete="CASCADE"), primary_key=True)
    user_id:    Mapped[str]        = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role:       Mapped[MemberRole] = mapped_column(Enum(MemberRole, name="member_role"), default=MemberRole.member, nullable=False)
    joined_at:  Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False)

    channel: Mapped["Channel"] = relationship("Channel", back_populates="members")


class Message(UUIDMixin, Base):
    __tablename__ = "msg_messages"

    channel_id:   Mapped[str]           = mapped_column(String(36), ForeignKey("msg_channels.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id:    Mapped[str|None]      = mapped_column(String(36), nullable=True)   # user_id or api_key_id
    sender_name:  Mapped[str]           = mapped_column(String(120), nullable=False)
    content:      Mapped[str]           = mapped_column(Text, nullable=False)
    source:       Mapped[MessageSource] = mapped_column(Enum(MessageSource, name="message_source"), default=MessageSource.user, nullable=False)
    api_key_id:   Mapped[str|None]      = mapped_column(String(36), nullable=True)
    created_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    expires_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    channel: Mapped["Channel"] = relationship("Channel", back_populates="messages")


class MessagingApiKey(UUIDMixin, TimestampMixin, Base):
    """Named API key for 3rd-party apps to post/read specific channels."""
    __tablename__ = "msg_api_keys"

    business_id:  Mapped[str]      = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name:         Mapped[str]      = mapped_column(String(100), nullable=False)
    key_hash:     Mapped[str]      = mapped_column(String(64), nullable=False, unique=True)  # SHA-256 hex
    permissions:  Mapped[list]     = mapped_column(JSON, default=list, nullable=False)        # ["read","write"]
    channel_ids:  Mapped[list]     = mapped_column(JSON, default=list, nullable=False)        # [] = all channels
    is_active:    Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_by:   Mapped[str|None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_used_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True), nullable=True)
