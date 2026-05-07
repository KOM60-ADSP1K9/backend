"""Abstract interface for the KategoriBarang repository."""

from abc import abstractmethod
from collections.abc import Iterable

from src.domain.entity.kategori_barang import KategoriBarang


class IKategoriBarangRepository:
    """Port for kategori barang read operations."""

    @abstractmethod
    async def get_all(self) -> Iterable[KategoriBarang]:
        """Fetch all kategori barang entities."""
