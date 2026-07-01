"""Blood donation and blood request models."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class BloodGroup(str, enum.Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"


class StatusEnum(str, enum.Enum):
    pending = "pending"
    fulfilled = "fulfilled"
    cancelled = "cancelled"


class BloodDonation(Base):
    __tablename__ = "blood_donations"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(String, unique=True, nullable=True)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blood_group = Column(Enum(BloodGroup), nullable=False)
    units = Column(Integer, default=1)
    city = Column(String, nullable=False)
    donation_time = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    donor = relationship("User", foreign_keys=[donor_id])


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id = Column(Integer, primary_key=True, index=True)
    needy_id = Column(String, unique=True, nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blood_group = Column(Enum(BloodGroup), nullable=False)
    units_needed = Column(Integer, default=1)
    city = Column(String, nullable=False)
    request_time = Column(String, nullable=True)
    urgency = Column(String, default="normal")
    notes = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    requester = relationship("User", foreign_keys=[requester_id])
