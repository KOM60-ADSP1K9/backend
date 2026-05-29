"""Usecase for listing the current user's notifications."""

from uuid import UUID

from src.domain.entity.i_notification_repository import INotificationRepository
from src.domain.entity.notification import Notification


class ListNotificationsRequest:
    def __init__(self, recipient_user_id: UUID) -> None:
        self.recipient_user_id = recipient_user_id


class ListNotificationsResult:
    def __init__(self, notifications: list[Notification], unread_count: int) -> None:
        self.notifications = notifications
        self.unread_count = unread_count


class ListNotificationsUsecase:
    """Return all notifications owned by the requesting user, newest first."""

    def __init__(self, notification_repository: INotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def execute(
        self, request: ListNotificationsRequest
    ) -> ListNotificationsResult:
        notifications = list(
            await self._notification_repository.findByRecipientUserId(
                request.recipient_user_id
            )
        )
        unread_count = await self._notification_repository.countUnread(
            request.recipient_user_id
        )
        return ListNotificationsResult(
            notifications=notifications,
            unread_count=unread_count,
        )
