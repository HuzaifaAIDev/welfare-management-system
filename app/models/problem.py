"""Problem / counseling request model."""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


class CategoryEnum(str, enum.Enum):
    family = "Family Issue"
    financial = "Financial Problem"
    medical = "Medical Issue"
    legal = "Legal Help"
    other = "Other"


class StatusEnum(str, enum.Enum):
    open = "open"
    in_review = "in_review"
    resolved = "resolved"


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, index=True)
    submitter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.open)
    admin_response = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submitter = relationship("User", foreign_keys=[submitter_id])
