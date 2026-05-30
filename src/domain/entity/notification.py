"""Domain model for notification."""

from dataclasses import dataclass
import datetime
import enum
from typing import Self
from uuid import UUID, uuid4


class NotificationType(str, enum.Enum):
    """Type of notification."""

    INQUIRY_RECEIVED = "inquiry_received"
    INQUIRY_SUBMITTED = "inquiry_submitted"
    INQUIRY_ACCEPTED = "inquiry_accepted"
    INQUIRY_REJECTED = "inquiry_rejected"


@dataclass
class Notification:
    """Notification domain model."""

    id: UUID
    recipient_user_id: UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool = False
    laporan_id: UUID | None = None
    inquiry_id: UUID | None = None
    read_at: datetime.datetime | None = None
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    @classmethod
    def New(
        cls,
        recipient_user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        laporan_id: UUID | None = None,
        inquiry_id: UUID | None = None,
    ) -> Self:
        """Create a new unread notification."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            recipient_user_id=recipient_user_id,
            type=type,
            title=title,
            message=message,
            is_read=False,
            laporan_id=laporan_id,
            inquiry_id=inquiry_id,
            read_at=None,
            created_at=now,
            updated_at=now,
        )

    def mark_read(self) -> None:
        """Mark this notification as read (idempotent)."""
        if self.is_read:
            return
        self.is_read = True
        self.read_at = datetime.datetime.now(datetime.timezone.utc)
