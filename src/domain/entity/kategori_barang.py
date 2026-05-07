"""Domain model for kategori barang."""

from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4


@dataclass
class KategoriBarang:
    """Kategori barang reference entity."""

    id: UUID
    name: str

    def __init__(self, id: UUID, name: str) -> None:
        self.id = id
        self.name = name

    @classmethod
    def New(cls, name: str) -> Self:
        """Create a new kategori barang."""
        return cls(id=uuid4(), name=name)
