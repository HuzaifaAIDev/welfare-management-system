"""Admin announcement/message model."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.session import Base


class AdminMessage(Base):
    __tablename__ = "admin_messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    audience = Column(String, nullable=False, default="all")  # 'donor' | 'needy' | 'all'
    created_at = Column(DateTime, default=datetime.utcnow)
