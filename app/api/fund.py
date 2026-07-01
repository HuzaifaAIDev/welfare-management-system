"""Fund donation and fund request endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.database.session import get_db
from app.models.fund import FundDonation, FundRequest
from app.models.user import RoleEnum, User
from app.schemas.fund import FundDonationCreate, FundDonationOut, FundRequestCreate, FundRequestOut
from app.utils.identifiers import format_id

router = APIRouter(prefix="/fund", tags=["Fund"])

ACTIVE_STATUSES = ("pending", "approved")


@router.post("/donate", response_model=FundDonationOut)
def add_fund_donation(
    data: FundDonationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.donor, RoleEnum.admin)),
) -> FundDonation:
    donation = FundDonation(**data.model_dump(), donor_id=current_user.id)
    db.add(donation)
    db.flush()
    donation.donation_id = format_id("FN", donation.id)
    db.commit()
    db.refresh(donation)
    return donation


@router.post("/request", response_model=FundRequestOut)
def request_fund(
    data: FundRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.needy, RoleEnum.admin)),
) -> FundRequest:
    existing = (
        db.query(FundRequest)
        .filter(FundRequest.requester_id == current_user.id, FundRequest.status.in_(ACTIVE_STATUSES))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="You already have an active fund request. Please wait for it to be processed before submitting another.",
        )
    fund_request = FundRequest(**data.model_dump(), requester_id=current_user.id)
    db.add(fund_request)
    db.flush()
    fund_request.needy_id = format_id("NR", fund_request.id)
    db.commit()
    db.refresh(fund_request)
    return fund_request


@router.get("/donations", response_model=List[FundDonationOut])
def get_donations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(FundDonation).all()
    return db.query(FundDonation).filter(FundDonation.donor_id == current_user.id).all()


@router.get("/requests", response_model=List[FundRequestOut])
def get_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.admin:
        return db.query(FundRequest).all()
    return db.query(FundRequest).filter(FundRequest.requester_id == current_user.id).all()


@router.patch("/requests/{request_id}/status")
def update_request_status(
    request_id: int,
    new_status: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    fund_request = db.query(FundRequest).filter(FundRequest.id == request_id).first()
    if not fund_request:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Request not found")
    fund_request.status = new_status
    db.commit()
    return {"message": "Status updated"}


@router.get("/summary")
def fund_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    total_donated = sum(d.amount for d in db.query(FundDonation).all())
    total_requested = sum(r.amount_needed for r in db.query(FundRequest).all())
    return {"total_donated": total_donated, "total_requested": total_requested}
