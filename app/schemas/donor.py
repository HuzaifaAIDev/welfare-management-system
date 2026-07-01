"""Pydantic schemas for blood donation / request endpoints."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BloodGroup(str, Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"


class BloodDonationCreate(BaseModel):
    blood_group: BloodGroup
    units: int = 1
    city: str
    notes: Optional[str] = None


class BloodDonationOut(BloodDonationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_id: Optional[str] = None
    donor_id: int
    status: str
    created_at: datetime


class BloodRequestCreate(BaseModel):
    blood_group: BloodGroup
    units_needed: int = 1
    city: str
    urgency: str = "normal"
    notes: Optional[str] = None


class BloodRequestOut(BloodRequestCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    needy_id: Optional[str] = None
    requester_id: int
    status: str
    created_at: datetime
