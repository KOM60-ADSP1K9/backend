"""Table that maps notification data."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.domain.entity.notification import Notification, NotificationType


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class NotificationTable(Base):
    """Notification representation in the database."""

    __tablename__ = "notification"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    type: Mapped[NotificationType] = mapped_column(
        Enum(
            NotificationType,
            name="notificationtype",
            values_callable=_enum_values,
        ),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String, nullable=False)

    message: Mapped[str] = mapped_column(String, nullable=False)

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Optional references to the originating entities.
    laporan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    inquiry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("inquiry.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_domain(self) -> Notification:
        return Notification(
            id=self.id,
            recipient_user_id=self.recipient_user_id,
            type=self.type,
            title=self.title,
            message=self.message,
            is_read=self.is_read,
            laporan_id=self.laporan_id,
            inquiry_id=self.inquiry_id,
            read_at=self.read_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, notification: Notification) -> "NotificationTable":
        return cls(
            id=notification.id,
            recipient_user_id=notification.recipient_user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            is_read=notification.is_read,
            laporan_id=notification.laporan_id,
            inquiry_id=notification.inquiry_id,
            read_at=notification.read_at,
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )
