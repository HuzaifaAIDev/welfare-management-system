"""Password hashing and JWT token utilities."""
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])"  # at least one lowercase
    r"(?=.*[A-Z])"  # at least one uppercase
    r"(?=.*\d)"  # at least one digit
    r"(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`])"  # at least one special char
    r".{8,}$"  # minimum 8 characters
)

PASSWORD_POLICY_MESSAGE = (
    "Password must be at least 8 characters and contain: an uppercase "
    "letter (A-Z), a lowercase letter (a-z), a number (0-9), and a special "
    "character (e.g. @, #, !, $). Example: Aa@12345"
)


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def is_password_strong(password: str) -> bool:
    """Return True if the password satisfies the strength policy."""
    return bool(PASSWORD_PATTERN.match(password))


def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token. Raises JWTError on failure."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


__all__ = [
    "hash_password",
    "verify_password",
    "is_password_strong",
    "create_access_token",
    "decode_access_token",
    "PASSWORD_POLICY_MESSAGE",
    "JWTError",
]
