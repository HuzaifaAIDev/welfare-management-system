"""Fund donation and fund request models."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class StatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class FundDonation(Base):
    __tablename__ = "fund_donations"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(String, unique=True, nullable=True)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    purpose = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    donor = relationship("User", foreign_keys=[donor_id])


class FundRequest(Base):
    __tablename__ = "fund_requests"

    id = Column(Integer, primary_key=True, index=True)
    needy_id = Column(String, unique=True, nullable=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount_needed = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    requester = relationship("User", foreign_keys=[requester_id])
