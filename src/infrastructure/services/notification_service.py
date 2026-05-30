"""In-app notification service.

Builds and persists notifications for domain events. All public methods are
best-effort: failures are logged and swallowed so the originating action
(e.g. creating an inquiry) is never broken by a notification problem.
"""

import logging
from uuid import UUID

from src.domain.entity.i_notification_repository import INotificationRepository
from src.domain.entity.inquiry import InquiryStatus, InquiryType
from src.domain.entity.notification import Notification, NotificationType

logger = logging.getLogger(__name__)

# Per-inquiry-type wording for the owner ("received") and sender ("submitted").
_INQUIRY_COPY: dict[InquiryType, dict[str, str]] = {
    InquiryType.CLAIM: {
        "owner_title": "Klaim baru pada laporan Anda",
        "owner_message": "Seseorang mengajukan klaim pada laporan temuan Anda.",
        "sender_title": "Klaim Anda terkirim",
        "sender_message": "Klaim Anda telah berhasil dikirim.",
    },
    InquiryType.FOUND: {
        "owner_title": "Laporan temuan baru pada laporan Anda",
        "owner_message": (
            "Seseorang melaporkan menemukan barang pada laporan kehilangan Anda."
        ),
        "sender_title": "Laporan temuan Anda terkirim",
        "sender_message": "Laporan temuan Anda telah berhasil dikirim.",
    },
}

# Per-resolution wording for the inquiry sender when the owner acts, keyed by
# inquiry type then status.
_STATUS_COPY: dict[InquiryType, dict[InquiryStatus, dict[str, str]]] = {
    InquiryType.CLAIM: {
        InquiryStatus.ACTIVE: {
            "title": "Klaim Anda diterima",
            "message": "Pemilik laporan menerima klaim Anda",
        },
        InquiryStatus.REJECTED: {
            "title": "Klaim Anda ditolak",
            "message": "Pemilik laporan menolak klaim Anda",
        },
    },
    InquiryType.FOUND: {
        InquiryStatus.ACTIVE: {
            "title": "Klaim temuan Anda diterima",
            "message": "Pemilik laporan menerima bukti temuan barang",
        },
        InquiryStatus.REJECTED: {
            "title": "Klaim temuan Anda ditolak",
            "message": "Pemilik laporan menolak bukti temuan barang",
        },
    },
}

_STATUS_TYPE: dict[InquiryStatus, NotificationType] = {
    InquiryStatus.ACTIVE: NotificationType.INQUIRY_ACCEPTED,
    InquiryStatus.REJECTED: NotificationType.INQUIRY_REJECTED,
}


class NotificationService:
    def __init__(self, notification_repository: INotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def notify_inquiry_created(
        self,
        *,
        owner_id: UUID | None,
        sender_id: UUID,
        laporan_id: UUID,
        inquiry_id: UUID,
        inquiry_type: InquiryType,
    ) -> None:
        try:
            copy = _INQUIRY_COPY[inquiry_type]

            notifications: list[Notification] = []
            if owner_id is not None:
                notifications.append(
                    Notification.New(
                        recipient_user_id=owner_id,
                        type=NotificationType.INQUIRY_RECEIVED,
                        title=copy["owner_title"],
                        message=copy["owner_message"],
                        laporan_id=laporan_id,
                        inquiry_id=inquiry_id,
                    )
                )
            if sender_id != owner_id:
                notifications.append(
                    Notification.New(
                        recipient_user_id=sender_id,
                        type=NotificationType.INQUIRY_SUBMITTED,
                        title=copy["sender_title"],
                        message=copy["sender_message"],
                        laporan_id=laporan_id,
                        inquiry_id=inquiry_id,
                    )
                )

            if notifications:
                await self._notification_repository.saveAll(notifications)
        except Exception:
            logger.exception(
                "Failed to create %s inquiry notifications for laporan %s",
                inquiry_type.value,
                laporan_id,
            )

    async def notify_inquiry_status_changed(
        self,
        *,
        sender_id: UUID,
        laporan_id: UUID,
        inquiry_id: UUID,
        inquiry_type: InquiryType,
        new_status: InquiryStatus,
    ) -> None:
        """Notify the inquiry sender when the owner accepts/rejects their inquiry."""
        copy = _STATUS_COPY.get(inquiry_type, {}).get(new_status)
        notification_type = _STATUS_TYPE.get(new_status)
        if copy is None or notification_type is None:
            return
        try:
            await self._notification_repository.save(
                Notification.New(
                    recipient_user_id=sender_id,
                    type=notification_type,
                    title=copy["title"],
                    message=copy["message"],
                    laporan_id=laporan_id,
                    inquiry_id=inquiry_id,
                )
            )
        except Exception:
            logger.exception(
                "Failed to create inquiry status notification for inquiry %s",
                inquiry_id,
            )
