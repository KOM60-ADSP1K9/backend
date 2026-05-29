"""Dependency providers for notification features."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_db_session
from src.domain.entity.i_notification_repository import INotificationRepository
from src.features.notification.usecase.list_notifications_usecase import (
    ListNotificationsUsecase,
)
from src.features.notification.usecase.mark_notification_read_usecase import (
    MarkNotificationReadUsecase,
)
from src.infrastructure.repositories.notification_repository import (
    NotificationRepository,
)


def get_notification_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> INotificationRepository:
    return NotificationRepository(db)


def get_list_notifications_usecase(
    notification_repository: INotificationRepository = Depends(
        get_notification_repository
    ),
) -> ListNotificationsUsecase:
    return ListNotificationsUsecase(notification_repository=notification_repository)


def get_mark_notification_read_usecase(
    notification_repository: INotificationRepository = Depends(
        get_notification_repository
    ),
) -> MarkNotificationReadUsecase:
    return MarkNotificationReadUsecase(notification_repository=notification_repository)
