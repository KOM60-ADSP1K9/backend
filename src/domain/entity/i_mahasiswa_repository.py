"""Abstract interface for the Mahasiswa repository."""

from abc import abstractmethod
from uuid import UUID

from src.domain.entity.user import Mahasiswa
from src.infrastructure.repositories.repository import IRepository


class IMahasiswaRepository(IRepository[Mahasiswa, UUID]):
    """Port for mahasiswa persistence with additional query methods."""

    @abstractmethod
    async def find_by_email(self, email: str) -> Mahasiswa | None:
        """Look up a mahasiswa by email address."""

    @abstractmethod
    async def update(self, entity: Mahasiswa) -> Mahasiswa:
        """Persist changes to an existing mahasiswa."""
