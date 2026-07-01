"""Food (rashan) donation and request models."""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


class StatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    distributed = "distributed"
    rejected = "rejected"


class FoodDonation(Base):
    __tablename__ = "food_donations"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(String, unique=True, nullable=True)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    rice_kg = Column(Float, nullable=True, default=0.0)
    flour_kg = Column(Float, nullable=True, default=0.0)
    oil_kg = Column(Float, nullable=True, default=0.0)
    sugar_kg = Column(Float, nullable=True, default=0.0)
    pulses_kg = Column(Float, nullable=True, default=0.0)

    items = Column(String, nullable=False)
    quantity_description = Column(String, nullable=True)
    city = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    is_fulfilled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    donor = relationship("User", foreign_keys=[donor_id])


class FoodRequest(Base):
    __tablename__ = "food_requests"

    id = Column(Integer, primary_key=True, index=True)
    needy_id = Column(String, unique=True, nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    rice_kg = Column(Float, nullable=True, default=0.0)
    flour_kg = Column(Float, nullable=True, default=0.0)
    oil_kg = Column(Float, nullable=True, default=0.0)
    sugar_kg = Column(Float, nullable=True, default=0.0)
    pulses_kg = Column(Float, nullable=True, default=0.0)

    items_needed = Column(String, nullable=False)
    family_members = Column(Integer, default=1)
    city = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    is_fulfilled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    requester = relationship("User", foreign_keys=[requester_id])
