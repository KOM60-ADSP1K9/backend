"""Table that maps lokasi data."""

import uuid

from sqlalchemy import Float, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base
from src.domain.entity.lokasi import Lokasi


class LokasiTable(Base):
    """Lokasi representation in the database."""

    __tablename__ = "lokasi"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    def to_domain(self) -> Lokasi:
        return Lokasi(
            id=self.id,
            name=self.name,
            latitude=self.latitude,
            longitude=self.longitude,
        )
