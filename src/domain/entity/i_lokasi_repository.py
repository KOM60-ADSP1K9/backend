"""Abstract interface for the Lokasi repository."""

from abc import abstractmethod
from collections.abc import Iterable

from src.domain.entity.lokasi import Lokasi


class ILokasiRepository:
    """Port for lokasi read operations."""

    @abstractmethod
    async def get_all(self) -> Iterable[Lokasi]:
        """Fetch all lokasi entities."""
