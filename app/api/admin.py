"""Admin endpoints: login, announcements, unified search, inventory, fulfillment."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import String, cast, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.security import create_access_token
from app.database.session import get_db
from app.models.admin import AdminMessage
from app.models.donor import BloodDonation, BloodRequest
from app.models.food import FoodDonation, FoodRequest
from app.models.fund import FundDonation, FundRequest
from app.models.problem import Problem
from app.models.user import RoleEnum, User
from app.schemas.admin import MessageCreate
from app.schemas.auth import AdminLoginRequest, Token
from app.schemas.food import FoodFulfillRequest
from app.services.admin_service import ensure_admin_exists
from app.services.inventory_service import add_stock, classify_food, get_or_create, remove_stock, snapshot
from app.utils.identifiers import format_id

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Admin login ──────────────────────────────────────────────────────────
@router.post("/login", response_model=Token)
def admin_login(data: AdminLoginRequest, db: Session = Depends(get_db)) -> Token:
    ensure_admin_exists(db)
    user = db.query(User).filter(User.email == settings.admin_email).first()

    from app.core.security import verify_password

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong admin password")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
        user_id=user.id,
    )


# ── Announcements ────────────────────────────────────────────────────────
@router.post("/message")
def post_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    audience = data.audience if data.audience in ("donor", "needy", "all") else "all"
    message = AdminMessage(message=data.message, audience=audience)
    db.add(message)
    db.commit()
    db.refresh(message)
    return {
        "id": message.id,
        "message": message.message,
        "audience": message.audience,
        "created_at": str(message.created_at),
    }


@router.get("/messages")
def get_messages(
    audience: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list:
    query = db.query(AdminMessage)
    if audience in ("donor", "needy"):
        query = query.filter(AdminMessage.audience.in_([audience, "all"]))
    messages = query.order_by(AdminMessage.created_at.desc()).limit(50).all()
    return [
        {"id": m.id, "message": m.message, "audience": m.audience, "created_at": str(m.created_at)}
        for m in messages
    ]


@router.delete("/messages/{message_id}")
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    message = db.query(AdminMessage).filter(AdminMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    db.delete(message)
    db.commit()
    return {"deleted": message_id}


# ── Unified search ───────────────────────────────────────────────────────
def _format_user(user: User) -> dict:
    role = str(user.role.value if hasattr(user.role, "value") else user.role)
    return {
        "id": user.id,
        "donor_id": format_id("DON", user.id) if role == "donor" else None,
        "needy_id": format_id("NEE", user.id) if role == "needy" else None,
        "display_id": (
            format_id("DON", user.id)
            if role == "donor"
            else format_id("NEE", user.id)
            if role == "needy"
            else "ADMIN"
        ),
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone,
        "age": user.age,
        "cnic": user.cnic,
        "role": role,
    }


@router.get("/search")
def unified_search(
    q: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> list:
    query = db.query(User).filter(User.email != settings.admin_email)
    if role in ("donor", "needy"):
        query = query.filter(User.role == role)
    if q:
        term = q.strip()
        numeric = term.upper().replace("DON-", "").replace("NEE-", "").lstrip("0") or "0"
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{term}%"),
                User.email.ilike(f"%{term}%"),
                User.cnic.ilike(f"%{term}%"),
                User.phone.ilike(f"%{term}%"),
                cast(User.id, String).ilike(f"%{numeric}%"),
            )
        )
    return [_format_user(u) for u in query.order_by(User.id.desc()).all()]


@router.get("/donors")
def search_donors(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> list:
    return unified_search(q=q, role="donor", db=db, current_user=current_user)


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> list:
    users = db.query(User).filter(User.email != settings.admin_email).all()
    return [_format_user(u) for u in users]


# ── All donations / requests ─────────────────────────────────────────────
@router.get("/all-donations")
def get_all_donations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    def donor_info(user_id: int) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        return {
            "donor_id": format_id("DON", user_id),
            "full_name": user.full_name if user else "Unknown",
            "phone": user.phone if user else None,
        }

    return {
        "blood": [
            {
                "id": d.id,
                "donation_id": d.donation_id or format_id("BD", d.id),
                "type": "blood",
                "donor": donor_info(d.donor_id),
                "blood_group": d.blood_group,
                "units": d.units,
                "city": d.city,
                "notes": d.notes,
                "status": d.status,
                "is_fulfilled": str(d.status) in ("fulfilled",),
                "created_at": str(d.created_at),
            }
            for d in db.query(BloodDonation).all()
        ],
        "fund": [
            {
                "id": d.id,
                "donation_id": d.donation_id or format_id("FN", d.id),
                "type": "fund",
                "donor": donor_info(d.donor_id),
                "amount": d.amount,
                "purpose": d.purpose,
                "notes": d.notes,
                "created_at": str(d.created_at),
            }
            for d in db.query(FundDonation).all()
        ],
        "food": [
            {
                "id": d.id,
                "donation_id": d.donation_id or format_id("FD", d.id),
                "type": "food",
                "donor": donor_info(d.donor_id),
                "items": d.items,
                "rice_kg": d.rice_kg or 0,
                "flour_kg": d.flour_kg or 0,
                "oil_kg": d.oil_kg or 0,
                "sugar_kg": d.sugar_kg or 0,
                "pulses_kg": d.pulses_kg or 0,
                "city": d.city,
                "notes": d.notes,
                "status": d.status,
                "is_fulfilled": d.is_fulfilled,
                "category": classify_food(d.items),
                "created_at": str(d.created_at),
            }
            for d in db.query(FoodDonation).all()
        ],
    }


@router.get("/all-requests")
def get_all_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    def requester_info(user_id: int) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        return {
            "needy_id": format_id("NEE", user_id),
            "full_name": user.full_name if user else "Unknown",
            "phone": user.phone if user else None,
        }

    return {
        "blood": [
            {
                "id": r.id,
                "needy_id": r.needy_id or format_id("BR", r.id),
                "requester": requester_info(r.requester_id),
                "blood_group": r.blood_group,
                "units_needed": r.units_needed,
                "city": r.city,
                "urgency": r.urgency,
                "notes": r.notes,
                "status": r.status,
                "is_fulfilled": str(r.status) in ("fulfilled",),
                "created_at": str(r.created_at),
            }
            for r in db.query(BloodRequest).all()
        ],
        "fund": [
            {
                "id": r.id,
                "needy_id": r.needy_id or format_id("NR", r.id),
                "requester": requester_info(r.requester_id),
                "amount_needed": r.amount_needed,
                "reason": r.reason,
                "notes": r.notes,
                "status": r.status,
                "is_fulfilled": str(r.status) in ("approved",),
                "created_at": str(r.created_at),
            }
            for r in db.query(FundRequest).all()
        ],
        "food": [
            {
                "id": r.id,
                "needy_id": r.needy_id or format_id("FR", r.id),
                "requester": requester_info(r.requester_id),
                "items_needed": r.items_needed,
                "rice_kg": r.rice_kg or 0,
                "flour_kg": r.flour_kg or 0,
                "oil_kg": r.oil_kg or 0,
                "sugar_kg": r.sugar_kg or 0,
                "pulses_kg": r.pulses_kg or 0,
                "family_members": r.family_members,
                "city": r.city,
                "notes": r.notes,
                "status": r.status,
                "is_fulfilled": r.is_fulfilled,
                "category": classify_food(r.items_needed),
                "created_at": str(r.created_at),
            }
            for r in db.query(FoodRequest).all()
        ],
        "problems": [
            {
                "id": p.id,
                "requester": requester_info(p.submitter_id),
                "title": p.title,
                "category": p.category,
                "description": p.description,
                "status": p.status,
                "admin_response": p.admin_response,
                "created_at": str(p.created_at),
            }
            for p in db.query(Problem).all()
        ],
    }


# ── Inventory ─────────────────────────────────────────────────────────────
@router.get("/inventory")
def get_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    return snapshot(db)


# ── Fulfill donation (adds to inventory) ──────────────────────────────────
@router.patch("/donations/{kind}/{donation_id}/fulfill")
def fulfill_donation(
    kind: str,
    donation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    if kind == "blood":
        donation = db.query(BloodDonation).filter(BloodDonation.id == donation_id).first()
        if not donation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        if str(donation.status) in ("fulfilled", "approved"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This donation has already been accepted into stock.")
        blood_group = donation.blood_group.value if hasattr(donation.blood_group, "value") else str(donation.blood_group)
        add_stock(db, "blood", blood_group, donation.units or 1)
        donation.status = "fulfilled"
        db.commit()
        return {"ok": True, "added": {"blood": {blood_group: donation.units}}}

    if kind == "food":
        donation = db.query(FoodDonation).filter(FoodDonation.id == donation_id).first()
        if not donation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        if donation.is_fulfilled or str(donation.status) in ("distributed", "approved"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This donation has already been accepted into stock.")
        added = {}
        items_map = [
            ("Rice", donation.rice_kg),
            ("Flour", donation.flour_kg),
            ("Oil", donation.oil_kg),
            ("Sugar", donation.sugar_kg),
            ("Pulses", donation.pulses_kg),
        ]
        for category, kg in items_map:
            kg = kg or 0
            if kg > 0:
                add_stock(db, "food", category, kg)
                added[category] = kg
        donation.status = "approved"
        donation.is_fulfilled = True
        db.commit()
        return {"ok": True, "added": {"food": added}}

    if kind == "fund":
        donation = db.query(FundDonation).filter(FundDonation.id == donation_id).first()
        if not donation:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        add_stock(db, "fund", "cash", donation.amount or 0)
        return {"ok": True, "added": {"fund": donation.amount}}

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown kind")


# ── Fulfill food request with admin-specified kg amounts ──────────────────
@router.patch("/requests/food/{request_id}/fulfill")
def fulfill_food_request(
    request_id: int,
    amounts: FoodFulfillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    food_request = db.query(FoodRequest).filter(FoodRequest.id == request_id).first()
    if not food_request:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if food_request.is_fulfilled or str(food_request.status) == "distributed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This request has already been distributed.")

    items_map = [
        ("Rice", amounts.rice_kg),
        ("Flour", amounts.flour_kg),
        ("Oil", amounts.oil_kg),
        ("Sugar", amounts.sugar_kg),
        ("Pulses", amounts.pulses_kg),
    ]
    total_to_give = sum(kg or 0 for _, kg in items_map)
    if total_to_give <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please specify at least one item amount to distribute.")

    insufficient = []
    for category, kg in items_map:
        if kg and kg > 0:
            row = get_or_create(db, "food", category)
            if (row.amount or 0) < kg:
                insufficient.append(f"{category}: need {kg}kg but only {row.amount or 0}kg in stock")
    if insufficient:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Insufficient stock:\n" + "\n".join(insufficient))

    given = {}
    for category, kg in items_map:
        if kg and kg > 0:
            remove_stock(db, "food", category, kg)
            given[category] = kg

    food_request.status = "distributed"
    food_request.is_fulfilled = True
    db.commit()
    return {"ok": True, "distributed": given}


# ── Fulfill other requests (blood, fund) ───────────────────────────────────
@router.patch("/requests/{kind}/{request_id}/fulfill")
def fulfill_request(
    kind: str,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    if kind == "food":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "For food requests use the food-specific fulfill endpoint with kg amounts.")

    if kind == "blood":
        blood_request = db.query(BloodRequest).filter(BloodRequest.id == request_id).first()
        if not blood_request:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        if str(blood_request.status) == "fulfilled":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This request has already been fulfilled.")
        blood_group = (
            blood_request.blood_group.value
            if hasattr(blood_request.blood_group, "value")
            else str(blood_request.blood_group)
        )
        ok = remove_stock(db, "blood", blood_group, blood_request.units_needed or 1)
        if not ok:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Not enough {blood_group} blood in inventory to fulfill this request.")
        blood_request.status = "fulfilled"
        db.commit()
        return {"ok": True}

    if kind == "fund":
        fund_request = db.query(FundRequest).filter(FundRequest.id == request_id).first()
        if not fund_request:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
        if str(fund_request.status) == "approved":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "This request has already been approved.")
        ok = remove_stock(db, "fund", "cash", fund_request.amount_needed or 0)
        if not ok:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not enough funds in inventory to fulfill this request.")
        fund_request.status = "approved"
        db.commit()
        return {"ok": True}

    raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown kind")


# ── Reject request ──────────────────────────────────────────────────────
_REJECT_MODEL_MAP = {
    "blood": (BloodRequest, "cancelled"),
    "food": (FoodRequest, "rejected"),
    "fund": (FundRequest, "rejected"),
}


@router.patch("/requests/{kind}/{request_id}/reject")
def reject_request(
    kind: str,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> dict:
    mapping = _REJECT_MODEL_MAP.get(kind)
    if not mapping:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown kind")
    model, new_status = mapping
    record = db.query(model).filter(model.id == request_id).first()
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    record.status = new_status
    db.commit()
    return {"ok": True}
