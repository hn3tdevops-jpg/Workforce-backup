from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from apps.api.app.db.session import Base


class Business(Base):
    __tablename__ = "businesses"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="free")
    settings_json = Column(Text, nullable=True)
    deleted_at = Column(DateTime, nullable=True)

    locations = relationship("Location", back_populates="business")


class Location(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String, ForeignKey("locations.id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    settings_json = Column(Text, nullable=True)

    business = relationship("Business", back_populates="locations")


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    primary_location_id = Column(String, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, nullable=False, default="active")

    __table_args__ = (
        UniqueConstraint('user_id', 'business_id', name='uq_membership_user_business'),
        Index('ix_membership_business_status', 'business_id', 'status'),
    )
