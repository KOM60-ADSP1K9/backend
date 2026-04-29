"""Abstract interface for the Laporan repository."""

from abc import abstractmethod
from uuid import UUID

from src.domain.entity.laporan import Laporan
from src.infrastructure.repositories.repository import IRepository


class ILaporanRepository(IRepository[Laporan, UUID]):
    """Port for laporan persistence."""

    @abstractmethod
    async def update(self, entity: Laporan) -> Laporan:
        """Persist changes to an existing laporan."""
