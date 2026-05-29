"""In-app notification service.

Builds and persists notifications for domain events. All public methods are
best-effort: failures are logged and swallowed so the originating action
(e.g. creating an inquiry) is never broken by a notification problem.
"""

import logging
from uuid import UUID

from src.domain.entity.i_notification_repository import INotificationRepository
from src.domain.entity.inquiry import InquiryType
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
