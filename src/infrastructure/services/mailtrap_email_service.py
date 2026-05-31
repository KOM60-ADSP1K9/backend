"""
Mailtrap email service implementation (mailtrap SDK, sending API).
"""

import asyncio
import logging
from uuid import UUID

import mailtrap as mt

from src.core.config import settings
from src.application.i_email_service import IEmailService
from src.domain.entity.inquiry import InquiryType
from src.infrastructure.services.email_templates import APP_NAME, render_email

logger = logging.getLogger(__name__)


class MailtrapEmailService(IEmailService):
    """Send transactional emails via the Mailtrap sending API."""

    def __init__(self) -> None:
        self._client = mt.MailtrapClient(token=settings.MAILTRAP_API_KEY)
        self._sender = mt.Address(email=settings.SMTP_FROM, name=APP_NAME)

    async def _send(self, *, to_email: str, subject: str, html_body: str) -> None:
        mail = mt.Mail(
            sender=self._sender,
            to=[mt.Address(email=to_email)],
            subject=subject,
            html=html_body,
        )
        # mailtrap SDK is synchronous; run off the event loop.
        await asyncio.to_thread(self._client.send, mail)

    async def send_verification_email(self, to_email: str, token: str) -> None:
        verify_url = f"{settings.BASE_URL}/auth/verify-email?token={token}"

        html_body = render_email(
            eyebrow="Verifikasi Akun",
            heading="Verifikasi alamat email Anda",
            paragraphs=[
                "Tekan tombol di bawah ini untuk memverifikasi alamat email Anda dan mengaktifkan akun.",
            ],
            cta_label="Verifikasi Email",
            cta_url=verify_url,
            footnote="Link ini akan kedaluwarsa dalam 10 menit. Abaikan email ini jika Anda tidak membuat akun.",
        )

        await self._send(
            to_email=to_email,
            subject="Verify Alamat Email Anda",
            html_body=html_body,
        )

    async def send_inquiry_notification(
        self,
        to_email: str,
        inquiry_type: InquiryType,
        laporan_id: UUID,
    ) -> None:
        laporan_url = f"{settings.FRONTEND_BASE_URL}/laporan/{laporan_id}"

        if inquiry_type == InquiryType.CLAIM:
            subject = "Klaim Baru untuk Laporan Temuan Anda"
            html_body = render_email(
                eyebrow="Klaim Baru",
                heading="Klaim baru untuk laporan temuan Anda",
                paragraphs=[
                    "Seseorang telah mengajukan klaim atas laporan temuan yang Anda buat.",
                    "Silakan periksa laporan Anda untuk melihat detail klaim dan menghubungi pengirim jika perlu.",
                ],
                cta_label="Lihat Detail Laporan",
                cta_url=laporan_url,
            )
        else:
            subject = "Laporan Hilang Anda Telah Ditemukan"
            html_body = render_email(
                eyebrow="Barang Ditemukan",
                heading="Laporan hilang Anda telah ditemukan",
                paragraphs=[
                    "Seseorang melaporkan telah menemukan barang dari laporan hilang Anda.",
                    "Silakan periksa laporan Anda untuk melihat detail temuan dan menghubungi pengirim jika perlu.",
                ],
                cta_label="Lihat Detail Laporan",
                cta_url=laporan_url,
            )

        await self._send(to_email=to_email, subject=subject, html_body=html_body)
