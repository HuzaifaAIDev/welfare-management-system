"""Pydantic schemas for food (rashan) donation / request endpoints."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class FoodDonationCreate(BaseModel):
    rice_kg: Optional[float] = 0.0
    flour_kg: Optional[float] = 0.0
    oil_kg: Optional[float] = 0.0
    sugar_kg: Optional[float] = 0.0
    pulses_kg: Optional[float] = 0.0
    city: str
    notes: Optional[str] = None

    @field_validator("rice_kg", "flour_kg", "oil_kg", "sugar_kg", "pulses_kg", mode="before")
    @classmethod
    def non_negative(cls, v):
        return max(0.0, float(v or 0))


class FoodDonationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_id: Optional[str] = None
    donor_id: int
    rice_kg: Optional[float] = 0.0
    flour_kg: Optional[float] = 0.0
    oil_kg: Optional[float] = 0.0
    sugar_kg: Optional[float] = 0.0
    pulses_kg: Optional[float] = 0.0
    items: str
    quantity_description: Optional[str] = None
    city: str
    notes: Optional[str] = None
    status: str
    is_fulfilled: bool = False
    created_at: datetime


class FoodRequestCreate(BaseModel):
    rice_kg: Optional[float] = 0.0
    flour_kg: Optional[float] = 0.0
    oil_kg: Optional[float] = 0.0
    sugar_kg: Optional[float] = 0.0
    pulses_kg: Optional[float] = 0.0
    family_members: int = 1
    city: str
    notes: Optional[str] = None

    @field_validator("rice_kg", "flour_kg", "oil_kg", "sugar_kg", "pulses_kg", mode="before")
    @classmethod
    def non_negative(cls, v):
        return max(0.0, float(v or 0))


class FoodRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    needy_id: Optional[str] = None
    requester_id: int
    rice_kg: Optional[float] = 0.0
    flour_kg: Optional[float] = 0.0
    oil_kg: Optional[float] = 0.0
    sugar_kg: Optional[float] = 0.0
    pulses_kg: Optional[float] = 0.0
    items_needed: str
    family_members: int
    city: str
    notes: Optional[str] = None
    status: str
    is_fulfilled: bool = False
    created_at: datetime


class FoodFulfillRequest(BaseModel):
    """Admin-specified kg amounts used to fulfill a food request from stock."""

    rice_kg: Optional[float] = 0.0
    flour_kg: Optional[float] = 0.0
    oil_kg: Optional[float] = 0.0
    sugar_kg: Optional[float] = 0.0
    pulses_kg: Optional[float] = 0.0
