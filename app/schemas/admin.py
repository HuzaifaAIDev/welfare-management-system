"""Pydantic schemas for admin endpoints (announcements, fulfillment)."""
from pydantic import BaseModel


class MessageCreate(BaseModel):
    message: str
    audience: str = "all"  # 'donor' | 'needy' | 'all'


class MessageOut(BaseModel):
    id: int
    message: str
    audience: str
    created_at: str
