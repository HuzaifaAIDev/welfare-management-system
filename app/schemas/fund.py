"""Pydantic schemas for fund donation / request endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FundDonationCreate(BaseModel):
    amount: float
    purpose: Optional[str] = None
    notes: Optional[str] = None


class FundDonationOut(FundDonationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_id: Optional[str] = None
    donor_id: int
    created_at: datetime


class FundRequestCreate(BaseModel):
    amount_needed: float
    reason: str
    notes: Optional[str] = None


class FundRequestOut(FundRequestCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    needy_id: Optional[str] = None
    requester_id: int
    status: str
    created_at: datetime
