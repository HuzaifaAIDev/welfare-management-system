"""Business logic for reading and mutating warehouse inventory levels."""
from sqlalchemy.orm import Session

from app.models.inventory import BLOOD_GROUPS, FOOD_CATEGORIES, Inventory


def classify_food(items_text: str) -> str:
    """Pick the best matching food category from free-text items."""
    if not items_text:
        return "Other"
    lowered = items_text.lower()
    for category in FOOD_CATEGORIES:
        if category.lower() in lowered:
            return category
    return "Other"


def get_or_create(db: Session, kind: str, category: str) -> Inventory:
    row = db.query(Inventory).filter(Inventory.kind == kind, Inventory.category == category).first()
    if not row:
        row = Inventory(kind=kind, category=category, amount=0)
        db.add(row)
        db.flush()
    return row


def add_stock(db: Session, kind: str, category: str, amount: float) -> None:
    row = get_or_create(db, kind, category)
    row.amount = (row.amount or 0) + float(amount)
    db.commit()


def remove_stock(db: Session, kind: str, category: str, amount: float) -> bool:
    """Subtract `amount` from stock. Returns False if there isn't enough stock."""
    row = get_or_create(db, kind, category)
    if (row.amount or 0) < float(amount):
        return False
    row.amount -= float(amount)
    db.commit()
    return True


def snapshot(db: Session) -> dict:
    """Return current inventory grouped by kind, food shown in kg."""
    rows = db.query(Inventory).all()
    out: dict = {"blood": {}, "food": {}, "fund": 0.0}
    for row in rows:
        if row.kind == "blood":
            out["blood"][row.category] = row.amount
        elif row.kind == "food":
            out["food"][row.category] = row.amount
        elif row.kind == "fund":
            out["fund"] = (out["fund"] or 0) + (row.amount or 0)

    for group in BLOOD_GROUPS:
        out["blood"].setdefault(group, 0)
    for category in FOOD_CATEGORIES:
        out["food"].setdefault(category, 0)
    return out
