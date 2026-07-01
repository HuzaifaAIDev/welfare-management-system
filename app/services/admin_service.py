"""Admin account bootstrap logic."""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import RoleEnum, User

logger = logging.getLogger(__name__)


def ensure_admin_exists(db: Session) -> None:
    """
    Create the default admin account if it does not already exist.

    The admin email/password are read from environment variables
    (ADMIN_EMAIL / ADMIN_PASSWORD) and the password is stored as a bcrypt
    hash — never in plain text.
    """
    existing = db.query(User).filter(User.email == settings.admin_email).first()
    if existing:
        return

    admin = User(
        full_name=settings.admin_full_name,
        email=settings.admin_email,
        phone=None,
        age=None,
        cnic=None,
        password_hash=hash_password(settings.admin_password),
        role=RoleEnum.admin,
    )
    db.add(admin)
    db.commit()
    logger.info("Default admin account created for %s", settings.admin_email)
