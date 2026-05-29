"""Notification controller.

GET   /notifications            – List the current user's notifications.
PATCH /notifications/{id}/read  – Mark one of the current user's notifications read.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from src.core.auth import get_current_user
from src.core.http import HTTPDataResponse
from src.domain.entity.notification import Notification, NotificationType
from src.domain.entity.user import User
from src.features.notification.notification_dependencies import (
    get_list_notifications_usecase,
    get_mark_notification_read_usecase,
)
from src.features.notification.usecase.list_notifications_usecase import (
    ListNotificationsRequest,
    ListNotificationsUsecase,
)
from src.features.notification.usecase.mark_notification_read_usecase import (
    MarkNotificationReadRequest,
    MarkNotificationReadUsecase,
)

notification_router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    recipient_user_id: UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool
    laporan_id: UUID | None = None
    inquiry_id: UUID | None = None
    read_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class NotificationListDto(BaseModel):
    notifications: list[NotificationResponseDto]
    unread_count: int


def _to_notification_response_dto(
    notification: Notification,
) -> NotificationResponseDto:
    return NotificationResponseDto(
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


@notification_router.get(
    "",
    response_model=HTTPDataResponse[NotificationListDto],
)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    usecase: ListNotificationsUsecase = Depends(get_list_notifications_usecase),
) -> HTTPDataResponse[NotificationListDto]:
    """Return the current user's notifications, newest first."""
    result = await usecase.execute(
        ListNotificationsRequest(recipient_user_id=current_user.id)
    )

    return HTTPDataResponse[NotificationListDto](
        status="success",
        data=NotificationListDto(
            notifications=[
                _to_notification_response_dto(n) for n in result.notifications
            ],
            unread_count=result.unread_count,
        ),
        message="Notifications retrieved successfully",
    )


@notification_router.patch(
    "/{notification_id}/read",
    response_model=HTTPDataResponse[NotificationResponseDto],
)
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    usecase: MarkNotificationReadUsecase = Depends(get_mark_notification_read_usecase),
) -> HTTPDataResponse[NotificationResponseDto]:
    """Mark one of the current user's notifications as read."""
    result = await usecase.execute(
        MarkNotificationReadRequest(
            notification_id=notification_id,
            current_user_id=current_user.id,
        )
    )

    return HTTPDataResponse[NotificationResponseDto](
        status="success",
        data=_to_notification_response_dto(result.notification),
        message="Notification marked as read",
    )
