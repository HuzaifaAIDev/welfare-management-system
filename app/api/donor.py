"""Blood donation and blood request endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.donor import BloodDonation, BloodRequest
from app.models.user import RoleEnum, User
from app.schemas.donor import BloodDonationCreate, BloodDonationOut, BloodRequestCreate, BloodRequestOut
from app.utils.identifiers import format_id

router = APIRouter(prefix="/blood", tags=["Blood Donation"])

ACTIVE_STATUSES = ("pending", "approved")


@router.post("/donate", response_model=BloodDonationOut)
def add_blood_donation(
    data: BloodDonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.donor, RoleEnum.admin)),
) -> BloodDonation:
    existing = (
        db.query(BloodDonation)
        .filter(BloodDonation.donor_id == current_user.id, BloodDonation.status.in_(ACTIVE_STATUSES))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="You already have an active blood donation. Please wait for it to be processed before submitting another.",
        )
    donation = BloodDonation(**data.model_dump(), donor_id=current_user.id)
    db.add(donation)
    db.flush()
    donation.donation_id = format_id("BD", donation.id)
    db.commit()
    db.refresh(donation)
    return donation


@router.post("/request", response_model=BloodRequestOut)
def request_blood(
    data: BloodRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.needy, RoleEnum.admin)),
) -> BloodRequest:
    existing = (
        db.query(BloodRequest)
        .filter(BloodRequest.requester_id == current_user.id, BloodRequest.status.in_(ACTIVE_STATUSES))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="You already have an active blood request. Please wait for it to be processed before submitting another.",
        )
    blood_request = BloodRequest(**data.model_dump(), requester_id=current_user.id)
    db.add(blood_request)
    db.flush()
    blood_request.needy_id = format_id("BR", blood_request.id)
    db.commit()
    db.refresh(blood_request)
    return blood_request


@router.get("/donations", response_model=List[BloodDonationOut])
def get_donations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(BloodDonation).all()
    return db.query(BloodDonation).filter(BloodDonation.donor_id == current_user.id).all()


@router.get("/requests", response_model=List[BloodRequestOut])
def get_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(BloodRequest).all()
    return db.query(BloodRequest).filter(BloodRequest.requester_id == current_user.id).all()


@router.patch("/donations/{donation_id}/status")
def update_donation_status(
    donation_id: int,
    new_status: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    donation = db.query(BloodDonation).filter(BloodDonation.id == donation_id).first()
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
    blood_request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
    if not blood_request:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Request not found")
    blood_request.status = new_status
    db.commit()
    return {"message": "Status updated"}
