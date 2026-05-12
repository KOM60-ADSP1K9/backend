"""Abstract interface for the KategoriBarang repository."""

from abc import abstractmethod
from collections.abc import Iterable
from uuid import UUID

from src.domain.entity.kategori_barang import KategoriBarang


class IKategoriBarangRepository:
    """Port for kategori barang read operations."""

    @abstractmethod
    async def get_all(self) -> Iterable[KategoriBarang]:
        """Fetch all kategori barang entities."""

    @abstractmethod
    async def find_by_id(self, kategori_id: UUID) -> KategoriBarang | None:
        """Fetch a kategori barang entity by id."""
