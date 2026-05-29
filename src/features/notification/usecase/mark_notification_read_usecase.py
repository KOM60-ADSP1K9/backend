"""Usecase for marking a notification as read."""

from uuid import UUID

from src.core.exceptions import NotFoundException
from src.domain.entity.i_notification_repository import INotificationRepository
from src.domain.entity.notification import Notification


class MarkNotificationReadRequest:
    def __init__(self, notification_id: UUID, current_user_id: UUID) -> None:
        self.notification_id = notification_id
        self.current_user_id = current_user_id


class MarkNotificationReadResult:
    def __init__(self, notification: Notification) -> None:
        self.notification = notification


class MarkNotificationReadUsecase:
    """Mark a single notification as read; only the recipient may do so."""

    def __init__(self, notification_repository: INotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def execute(
        self, request: MarkNotificationReadRequest
    ) -> MarkNotificationReadResult:
        # Scope the lookup to the requesting user so notifications owned by
        # other users are indistinguishable from non-existent ones.
        notification = await self._notification_repository.findByIdAndUserId(
            request.notification_id, request.current_user_id
        )
        if notification is None:
            raise NotFoundException("Notification tidak ditemukan")

        notification.mark_read()
        saved = await self._notification_repository.update(notification)
        return MarkNotificationReadResult(notification=saved)
