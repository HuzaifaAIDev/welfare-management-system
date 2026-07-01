"""User model — covers admin, donor, and needy roles."""
import enum

from sqlalchemy import Column, Enum, Integer, String

from app.database.session import Base


class RoleEnum(str, enum.Enum):
    admin = "admin"
    donor = "donor"
    needy = "needy"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    cnic = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.needy, nullable=False)
