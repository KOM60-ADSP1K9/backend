"""Abstract interface for the Staff repository."""

from abc import abstractmethod
from uuid import UUID

from src.domain.entity.user import Staff
from src.infrastructure.repositories.repository import IRepository


class IStaffRepository(IRepository[Staff, UUID]):
    """Port for staff persistence with additional query methods."""

    @abstractmethod
    async def find_by_email(self, email: str) -> Staff | None:
        """Look up a staff by email address."""

    @abstractmethod
    async def update(self, entity: Staff) -> Staff:
        """Persist changes to an existing staff."""
