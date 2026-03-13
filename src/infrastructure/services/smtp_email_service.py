"""
SMTP email service implementation (fastapi-mail).
"""

import logging

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import NameEmail, SecretStr

from src.core.config import settings

logger = logging.getLogger(__name__)

_mail_conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=SecretStr(settings.SMTP_PASSWORD),
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_FROM=settings.SMTP_FROM,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
)


class SmtpEmailService:
    """Send transactional emails via SMTP using fastapi-mail."""

    async def send_verification_email(self, to_email: str, token: str) -> None:
        verify_url = f"{settings.BASE_URL}/auth/verify-email?token={token}"

        html_body = (
            "<h2>Email Verification</h2>"
            "<p>Tekan link di bawah ini untuk memverifikasi alamat email Anda:</p>"
            f'<p><a href="{verify_url}">{verify_url}</a></p>'
            f"<p>Link ini akan kedaluwarsa dalam {settings.JWT_EXPIRES_MINUTES} menit.</p>"
        )

        message = MessageSchema(
            subject="Verify Alamat Email Anda",
            recipients=[NameEmail(name="", email=to_email)],
            body=html_body,
            subtype=MessageType.html,
        )

        fm = FastMail(_mail_conf)
        await fm.send_message(message)
