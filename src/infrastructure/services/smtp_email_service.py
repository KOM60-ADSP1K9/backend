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

_APP_NAME = "Lost & Found"

_FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
_MONO_STACK = "'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"


def _render_email(
    *,
    eyebrow: str,
    heading: str,
    paragraphs: list[str],
    cta_label: str,
    cta_url: str,
    footnote: str | None = None,
) -> str:
    """Wrap email content"""
    body_paragraphs = "".join(
        f'<p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#1a1a1a;">{text}</p>'
        for text in paragraphs
    )

    footnote_block = (
        f'<p style="margin:24px 0 0;font-size:12px;line-height:1.5;color:#8a8a8a;">{footnote}</p>'
        if footnote
        else ""
    )

    return f"""\
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:{_FONT_STACK};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f4f4;">
<tr>
<td align="center" style="padding:40px 16px;">
<table role="presentation" width="520" cellpadding="0" cellspacing="0" style="width:520px;max-width:100%;background-color:#ffffff;border:1px solid #e6e6e6;">
<tr>
<td style="background-color:#000000;padding:20px 36px;">
<span style="font-family:{_MONO_STACK};font-size:13px;font-weight:600;letter-spacing:4px;color:#ffffff;text-transform:uppercase;">{_APP_NAME}</span>
</td>
</tr>
<tr>
<td style="padding:40px 36px 36px;">
<p style="margin:0 0 12px;font-family:{_MONO_STACK};font-size:11px;font-weight:600;letter-spacing:3px;color:#9a9a9a;text-transform:uppercase;">{eyebrow}</p>
<h1 style="margin:0 0 24px;font-size:24px;line-height:1.25;font-weight:700;color:#000000;letter-spacing:-0.4px;">{heading}</h1>
{body_paragraphs}
<table role="presentation" cellpadding="0" cellspacing="0" style="margin:28px 0 8px;">
<tr>
<td style="background-color:#000000;">
<a href="{cta_url}" style="display:inline-block;padding:14px 32px;font-size:14px;font-weight:600;letter-spacing:0.5px;color:#ffffff;text-decoration:none;">{cta_label}</a>
</td>
</tr>
</table>
<p style="margin:16px 0 0;font-family:{_MONO_STACK};font-size:12px;line-height:1.5;color:#6a6a6a;word-break:break-all;">{cta_url}</p>
{footnote_block}
</td>
</tr>
<tr>
<td style="border-top:1px solid #e6e6e6;padding:24px 36px;">
<p style="margin:0;font-size:11px;line-height:1.5;color:#9a9a9a;">Email otomatis dari {_APP_NAME}. Mohon tidak membalas pesan ini.</p>
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""


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

        html_body = _render_email(
            eyebrow="Verifikasi Akun",
            heading="Verifikasi alamat email Anda",
            paragraphs=[
                "Tekan tombol di bawah ini untuk memverifikasi alamat email Anda dan mengaktifkan akun.",
            ],
            cta_label="Verifikasi Email",
            cta_url=verify_url,
            footnote="Link ini akan kedaluwarsa dalam 10 menit. Abaikan email ini jika Anda tidak membuat akun.",
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
            html_body = _render_email(
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
            html_body = _render_email(
                eyebrow="Barang Ditemukan",
                heading="Laporan hilang Anda telah ditemukan",
                paragraphs=[
                    "Seseorang melaporkan telah menemukan barang dari laporan hilang Anda.",
                    "Silakan periksa laporan Anda untuk melihat detail temuan dan menghubungi pengirim jika perlu.",
                ],
                cta_label="Lihat Detail Laporan",
                cta_url=laporan_url,
            )

        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_body,
            subtype=MessageType.html,
        )

        fm = FastMail(_mail_conf)
        await fm.send_message(message)
