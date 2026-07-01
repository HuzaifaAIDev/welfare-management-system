"""Pydantic schemas for problem / counseling endpoints."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CategoryEnum(str, Enum):
    family = "Family Issue"
    financial = "Financial Problem"
    medical = "Medical Issue"
    legal = "Legal Help"
    other = "Other"


class ProblemCreate(BaseModel):
    title: str
    category: CategoryEnum
    description: str


class ProblemOut(ProblemCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submitter_id: int
    status: str
    admin_response: Optional[str] = None
    created_at: datetime


class AdminResponseUpdate(BaseModel):
    admin_response: str
    status: str
