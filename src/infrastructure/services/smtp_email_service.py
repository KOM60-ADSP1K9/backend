"""
SMTP email service implementation (fastapi-mail).
"""

import logging
from uuid import UUID

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import SecretStr

from src.core.config import settings
from src.application.i_email_service import IEmailService
from src.domain.entity.inquiry import InquiryType

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


class SmtpEmailService(IEmailService):
    """Send transactional emails via SMTP using fastapi-mail."""

    async def send_verification_email(self, to_email: str, token: str) -> None:
        verify_url = f"{settings.BASE_URL}/auth/verify-email?token={token}"

        html_body = (
            "<h2>Email Verification</h2>"
            "<p>Tekan link di bawah ini untuk memverifikasi alamat email Anda:</p>"
            f'<p><a href="{verify_url}">{verify_url}</a></p>'
            f"<p>Link ini akan kedaluwarsa dalam 10 menit.</p>"
        )

        message = MessageSchema(
            subject="Verify Alamat Email Anda",
            recipients=[to_email],
            body=html_body,
            subtype=MessageType.html,
        )

        fm = FastMail(_mail_conf)
        await fm.send_message(message)

    async def send_inquiry_notification(
        self,
        to_email: str,
        inquiry_type: InquiryType,
        laporan_id: UUID,
    ) -> None:
        laporan_url = f"{settings.FRONTEND_BASE_URL}/laporan/{laporan_id}"

        if inquiry_type == InquiryType.CLAIM:
            subject = "Klaim Baru untuk Laporan Temuan Anda"
            intro = (
                "Seseorang telah mengajukan klaim atas laporan temuan yang Anda buat."
            )
            html_body = (
                f"<h2>{subject}</h2>"
                f"<p>{intro}</p>"
                f"<p>Silakan periksa laporan Anda untuk melihat detail klaim dan menghubungi pengirim jika perlu.</p>"
                "<p>Tekan link di bawah ini untuk melihat detail laporan dan inquiry:</p>"
                f'<p><a href="{laporan_url}">{laporan_url}</a></p>'
            )
        else:
            subject = "Laporan Hilang Anda Telah Ditemukan"
            intro = (
                "Seseorang melaporkan telah menemukan barang dari laporan hilang Anda."
            )
            html_body = (
                f"<h2>{subject}</h2>"
                f"<p>{intro}</p>"
                f"<p>Silakan periksa laporan Anda untuk melihat detail temuan barang anda dan menghubungi pengirim jika perlu.</p>"
                "<p>Tekan link di bawah ini untuk melihat detail laporan dan inquiry:</p>"
                f'<p><a href="{laporan_url}">{laporan_url}</a></p>'
            )

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_body,
            subtype=MessageType.html,
        )

        fm = FastMail(_mail_conf)
        await fm.send_message(message)
