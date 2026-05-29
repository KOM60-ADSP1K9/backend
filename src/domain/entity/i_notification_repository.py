"""Abstract interface for the Notification repository."""

from abc import abstractmethod
from collections.abc import Iterable
from uuid import UUID

from src.domain.entity.notification import Notification
from src.infrastructure.repositories.repository import IRepository


class INotificationRepository(IRepository[Notification, UUID]):
    """Port for notification persistence."""

    @abstractmethod
    async def update(self, entity: Notification) -> Notification:
        """Persist changes to an existing notification."""

    @abstractmethod
    async def findByIdAndUserId(
        self, id: UUID, recipient_user_id: UUID
    ) -> Notification | None:
        """Return a notification owned by *recipient_user_id*, or None."""

    @abstractmethod
    async def findByRecipientUserId(
        self, recipient_user_id: UUID
    ) -> Iterable[Notification]:
        """Return all notifications for a recipient, newest first."""

    @abstractmethod
    async def countUnread(self, recipient_user_id: UUID) -> int:
        """Return number of unread notifications for a recipient."""
