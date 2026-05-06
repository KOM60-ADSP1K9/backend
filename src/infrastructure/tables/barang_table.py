"""Table that maps barang data."""

import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.domain.entity.barang import Barang

if TYPE_CHECKING:
    from src.infrastructure.tables.laporan_table import LaporanTable


class BarangTable(Base):
    """Barang representation in the database."""

    __tablename__ = "barang"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[str] = mapped_column(String, nullable=False)

    photo: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    laporan: Mapped["LaporanTable"] = relationship(
        "LaporanTable",
        back_populates="barang",
    )

    def to_domain(self) -> Barang:
        return Barang(
            id=self.id,
            name=self.name,
            description=self.description,
            photo=self.photo,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, barang: Barang, laporan_id: uuid.UUID) -> "BarangTable":
        """Convert a domain model to the mapped table model."""
        return cls(
            id=barang.id,
            laporan_id=laporan_id,
            name=barang.name,
            description=barang.description,
            photo=barang.photo,
            created_at=barang.created_at,
            updated_at=barang.updated_at,
        )
