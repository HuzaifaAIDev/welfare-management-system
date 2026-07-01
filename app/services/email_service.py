"""
Centralized module for all outbound email operations in the Welfare
Management System.

Configuration (SMTP host/port, sender address, and app password) is loaded
exclusively from environment variables — see `.env.example`. No credentials
are hardcoded in source.
"""
import logging
import secrets
import smtplib
import ssl
import string
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str, html: Optional[str] = None) -> tuple[bool, str]:
    """
    Send a plain-text (and optional HTML) email from the configured sender
    account via SMTP.

    Returns (success, message). `message` contains the error description
    when success is False — useful for surfacing in API responses / logs.
    """
    if not settings.smtp_sender_email or not settings.smtp_password:
        msg = (
            "SMTP is not configured. Set SMTP_SENDER_EMAIL and SMTP_PASSWORD "
            "in your environment / .env file to enable outbound email."
        )
        logger.warning(msg)
        return False, msg

    message = EmailMessage()
    message["From"] = settings.smtp_sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)
    if html:
        message.add_alternative(html, subtype="html")

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context, timeout=20) as server:
            server.login(settings.smtp_sender_email, settings.smtp_password)
            server.send_message(message)
        logger.info("Email sent to %s", to_email)
        return True, "ok"
    except smtplib.SMTPAuthenticationError as exc:
        err = f"SMTP authentication failed for {settings.smtp_sender_email}: {exc}"
        logger.error(err)
        return False, err
    except Exception as exc:  # noqa: BLE001 - surfaced to caller as an error message
        err = f"SMTP send failed: {type(exc).__name__}: {exc}"
        logger.error(err)
        return False, err


def generate_temporary_password(length: int = 10) -> str:
    """Generate a strong random password matching the app's password policy."""
    alphabet = string.ascii_letters + string.digits
    specials = "!@#$%^&*"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length - 2))
        pwd += secrets.choice(specials)
        pwd += secrets.choice(string.digits)
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
            and any(c in specials for c in pwd)
        ):
            return pwd


def send_password_reset_email(to_email: str, full_name: str, temporary_password: str) -> tuple[bool, str]:
    """Email a newly generated temporary password to the user."""
    subject = "Welfare Management System — Password Reset"
    body = (
        f"Dear {full_name},\n\n"
        f"We received a request to reset your password for the Welfare "
        f"Management System.\n\n"
        f"Your new temporary password is:\n\n"
        f"    {temporary_password}\n\n"
        f"Please log in and change it as soon as possible. Do not share it "
        f"with anyone.\n\n"
        f"If you did not request this, please contact the admin immediately.\n\n"
        f"— Welfare Management System"
    )
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;max-width:520px;
                margin:auto;padding:24px;border:1px solid #e5e7eb;
                border-radius:12px;background:#f0fdf4;">
      <h2 style="color:#15803d;margin-top:0;">Password Reset</h2>
      <p>Dear <b>{full_name}</b>,</p>
      <p>We received a request to reset your password for the
         <b>Welfare Management System</b>.</p>
      <p>Your new temporary password is:</p>
      <div style="background:#fff;border:1px dashed #16a34a;padding:12px;
                  text-align:center;font-size:18px;font-weight:700;
                  letter-spacing:1px;border-radius:8px;color:#14532d;">
         {temporary_password}
      </div>
      <p style="margin-top:18px;">Please log in and change it as soon as
         possible. Do not share it with anyone.</p>
      <p style="font-size:12px;color:#6b7280;">
         If you did not request this, please contact the admin immediately.
      </p>
    </div>
    """
    return send_email(to_email, subject, body, html=html)
