"""Table that maps kategori barang data."""

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.domain.entity.kategori_barang import KategoriBarang


class KategoriBarangTable(Base):
    """Kategori barang representation in the database."""

    __tablename__ = "kategori_barang"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    def to_domain(self) -> KategoriBarang:
        return KategoriBarang(
            id=self.id,
            name=self.name,
        )

    @classmethod
    def from_domain(cls, kategori_barang: KategoriBarang) -> "KategoriBarangTable":
        """Convert a domain model to the mapped table model."""
        return cls(
            id=kategori_barang.id,
            name=kategori_barang.name,
        )
