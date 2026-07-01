"""Food (rashan) donation and request endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.food import FoodDonation, FoodRequest
from app.models.user import RoleEnum, User
from app.schemas.food import FoodDonationCreate, FoodDonationOut, FoodRequestCreate, FoodRequestOut
from app.utils.identifiers import format_id

router = APIRouter(prefix="/food", tags=["Food / Rashan"])

ACTIVE_STATUSES = ("pending", "approved")


def _build_items_string(
    rice_kg: Optional[float],
    flour_kg: Optional[float],
    oil_kg: Optional[float],
    sugar_kg: Optional[float],
    pulses_kg: Optional[float],
) -> str:
    parts = []
    if rice_kg and rice_kg > 0:
        parts.append(f"Rice {rice_kg}kg")
    if flour_kg and flour_kg > 0:
        parts.append(f"Flour {flour_kg}kg")
    if oil_kg and oil_kg > 0:
        parts.append(f"Oil {oil_kg}kg")
    if sugar_kg and sugar_kg > 0:
        parts.append(f"Sugar {sugar_kg}kg")
    if pulses_kg and pulses_kg > 0:
        parts.append(f"Pulses {pulses_kg}kg")
    return ", ".join(parts) if parts else "No items specified"


@router.post("/donate", response_model=FoodDonationOut)
def add_food_donation(
    data: FoodDonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.donor, RoleEnum.admin)),
) -> FoodDonation:
    existing = (
        db.query(FoodDonation)
        .filter(FoodDonation.donor_id == current_user.id, FoodDonation.status.in_(ACTIVE_STATUSES))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="You already have an active donation request. Please wait for it to be processed before submitting another.",
        )

    total = (data.rice_kg or 0) + (data.flour_kg or 0) + (data.oil_kg or 0) + (data.sugar_kg or 0) + (data.pulses_kg or 0)
    if total <= 0:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Please specify at least one item with quantity (kg).")

    items_str = _build_items_string(data.rice_kg, data.flour_kg, data.oil_kg, data.sugar_kg, data.pulses_kg)

    donation = FoodDonation(
        donor_id=current_user.id,
        rice_kg=data.rice_kg or 0,
        flour_kg=data.flour_kg or 0,
        oil_kg=data.oil_kg or 0,
        sugar_kg=data.sugar_kg or 0,
        pulses_kg=data.pulses_kg or 0,
        items=items_str,
        quantity_description=f"Total: {total}kg",
        city=data.city,
        notes=data.notes,
    )
    db.add(donation)
    db.flush()
    donation.donation_id = format_id("FD", donation.id)
    db.commit()
    db.refresh(donation)
    return donation


@router.post("/request", response_model=FoodRequestOut)
def request_food(
    data: FoodRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.needy, RoleEnum.admin)),
) -> FoodRequest:
    existing = (
        db.query(FoodRequest)
        .filter(FoodRequest.requester_id == current_user.id, FoodRequest.status.in_(ACTIVE_STATUSES))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="You already have an active rashan request. Please wait for it to be processed before submitting another.",
        )

    total = (data.rice_kg or 0) + (data.flour_kg or 0) + (data.oil_kg or 0) + (data.sugar_kg or 0) + (data.pulses_kg or 0)
    if total <= 0:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Please specify at least one item with quantity (kg).")

    items_str = _build_items_string(data.rice_kg, data.flour_kg, data.oil_kg, data.sugar_kg, data.pulses_kg)

    food_request = FoodRequest(
        requester_id=current_user.id,
        rice_kg=data.rice_kg or 0,
        flour_kg=data.flour_kg or 0,
        oil_kg=data.oil_kg or 0,
        sugar_kg=data.sugar_kg or 0,
        pulses_kg=data.pulses_kg or 0,
        items_needed=items_str,
        family_members=data.family_members,
        city=data.city,
        notes=data.notes,
    )
    db.add(food_request)
    db.flush()
    food_request.needy_id = format_id("FR", food_request.id)
    db.commit()
    db.refresh(food_request)
    return food_request


@router.get("/donations", response_model=List[FoodDonationOut])
def get_donations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(FoodDonation).all()
    return db.query(FoodDonation).filter(FoodDonation.donor_id == current_user.id).all()


@router.get("/requests", response_model=List[FoodRequestOut])
def get_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(FoodRequest).all()
    return db.query(FoodRequest).filter(FoodRequest.requester_id == current_user.id).all()


@router.patch("/donations/{donation_id}/status")
def update_donation_status(
    donation_id: int,
    new_status: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    donation = db.query(FoodDonation).filter(FoodDonation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Donation not found")
    donation.status = new_status
    db.commit()
    return {"message": "Status updated"}


@router.patch("/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    new_status: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    food_request = db.query(FoodRequest).filter(FoodRequest.id == request_id).first()
    if not food_request:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Request not found")
    food_request.status = new_status
    db.commit()
    return {"message": "Status updated"}
