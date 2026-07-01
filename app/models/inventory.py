"""
Inventory model: tracks how many kg/units/PKR the welfare organization
currently holds, by category.

- Blood: keyed by blood group ('A+', 'O-', etc.) — units
- Food:  keyed by item ('Rice', 'Flour', 'Oil', 'Sugar', 'Pulses') — kg
- Fund:  single 'cash' bucket — PKR amount

Fulfilling a DONATION adds kg/units to inventory.
Fulfilling a needy REQUEST subtracts the admin-specified kg from inventory.
"""
from sqlalchemy import Column, Float, Integer, String, UniqueConstraint

from app.database.session import Base

FOOD_CATEGORIES = ["Rice", "Flour", "Oil", "Sugar", "Pulses"]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False)  # 'blood' | 'food' | 'fund'
    category = Column(String, nullable=False)  # e.g. 'A+', 'Rice', 'cash'
    amount = Column(Float, nullable=False, default=0)  # units / kg / PKR

    __table_args__ = (UniqueConstraint("kind", "category", name="uq_kind_category"),)
