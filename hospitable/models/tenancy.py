from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, func, text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    locations = relationship("Location", back_populates="business", cascade="all, delete-orphan")
    memberships = relationship("Membership", back_populates="business", cascade="all, delete-orphan")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(String(512))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    business = relationship("Business", back_populates="locations")

class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint('business_id', 'user_id', name='uix_business_user'),)

    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, server_default="member")
    is_active = Column(Boolean, nullable=False, server_default=text('true'))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    business = relationship("Business", back_populates="memberships")
