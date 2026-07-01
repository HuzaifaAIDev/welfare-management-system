"""Pydantic schemas for authentication endpoints."""
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.user import RoleEnum


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    age: Optional[int] = None
    cnic: Optional[str] = None
    password: str
    role: RoleEnum = RoleEnum.needy


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    user_id: int


class UserProfile(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    age: Optional[int] = None
    cnic: Optional[str] = None
    role: str
    donor_id: Optional[str] = None
    needy_id: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ChangePasswordRequest(BaseModel):
    """Payload for an authenticated user changing their own password.

    The user's identity is always taken from the JWT (see
    ``get_current_user``) — never from this payload — so there is no user
    ID field here by design.
    """

    current_password: str
    new_password: str
    confirm_password: str


class ChangePasswordResponse(BaseModel):
    message: str


class AdminLoginRequest(BaseModel):
    """Matches the existing frontend contract: password-only admin login.

    The admin's email is not user-supplied; it is resolved server-side from
    the single bootstrapped admin account (see ADMIN_EMAIL setting).
    """

    password: str
