"""Abstract interface for the Lokasi repository."""

from abc import abstractmethod
from collections.abc import Iterable
from uuid import UUID

from src.domain.entity.lokasi import Lokasi


class ILokasiRepository:
    """Port for lokasi read operations."""

    @abstractmethod
    async def get_all(self) -> Iterable[Lokasi]:
        """Fetch all lokasi entities."""

    @abstractmethod
    async def find_by_id(self, lokasi_id: UUID) -> Lokasi | None:
        """Fetch a lokasi entity by id."""

    @abstractmethod
    async def find_all_by_ids(self, lokasi_ids: Iterable[UUID]) -> Iterable[Lokasi]:
        """Fetch multiple lokasi entities by ids."""
