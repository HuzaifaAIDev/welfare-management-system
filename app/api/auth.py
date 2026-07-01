"""Authentication endpoints: register, login, current-user profile, password reset."""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import (
    PASSWORD_POLICY_MESSAGE,
    create_access_token,
    hash_password,
    is_password_strong,
    verify_password,
)
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    ForgotPasswordRequest,
    RegisterRequest,
    Token,
    UserProfile,
)
from app.services.email_service import generate_temporary_password, send_password_reset_email
from app.utils.identifiers import format_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _issue_token(user: User) -> Token:
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        full_name=user.full_name,
        user_id=user.id,
    )


@router.post("/register", response_model=Token)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> Token:
    if not is_password_strong(payload.password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_POLICY_MESSAGE)

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        age=payload.age,
        cnic=payload.cnic,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_token(user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return _issue_token(user)


@router.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return UserProfile(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        age=current_user.age,
        cnic=current_user.cnic,
        role=current_user.role,
        donor_id=format_id("DON", current_user.id) if current_user.role == "donor" else None,
        needy_id=format_id("NEE", current_user.id) if current_user.role == "needy" else None,
    )


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    """
    Reset the user's password to a freshly generated temporary password and
    email it to their registered address. The plain-text password is never
    stored — only its bcrypt hash.
    """
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account is registered with this email address.",
        )

    temporary_password = generate_temporary_password()
    user.password_hash = hash_password(temporary_password)
    db.commit()

    sent, error = send_password_reset_email(user.email, user.full_name, temporary_password)
    if not sent:
        logger.error("Failed to send password reset email to %s: %s", user.email, error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not send password email. {error}",
        )

    return {"message": f"A new password has been sent to {user.email}. Please check your inbox (and Spam folder)."}


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChangePasswordResponse:
    """
    Change the password of the currently authenticated user.

    The target user is resolved exclusively from the JWT access token via
    ``get_current_user`` — the client can never supply a user ID. The
    current password is re-verified against the stored bcrypt hash before
    any change is made, and the new password is validated against the same
    strength policy enforced at registration.

    No password value (current, new, or confirm) is ever logged, and error
    messages are kept generic so they cannot be used to enumerate accounts
    or infer why validation failed beyond what the user needs to fix it.
    """
    new_password = payload.new_password
    confirm_password = payload.confirm_password
    current_password = payload.current_password

    if not current_password or not new_password or not confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password, new password, and confirm password are all required.",
        )

    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match.",
        )

    if not is_password_strong(new_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_POLICY_MESSAGE)

    # Verify the caller actually knows the current password before allowing
    # any change. This must happen before the "must differ" check below so
    # we don't leak whether a guessed password matches via a different
    # error path.
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    if verify_password(new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )

    try:
        current_user.password_hash = hash_password(new_password)
        db.add(current_user)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to update password for user id %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not change password. Please try again later.",
        )

    return ChangePasswordResponse(message="Password changed successfully.")
