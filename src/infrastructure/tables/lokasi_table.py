"""Table that maps lokasi data."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.domain.entity.lokasi import Lokasi

if TYPE_CHECKING:
    from src.infrastructure.tables.user_table import UserTable


class LokasiTable(Base):
    """Lokasi representation in the database."""

    __tablename__ = "lokasi"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    supervisors: Mapped[list["UserTable"]] = relationship(
        "UserTable",
        back_populates="supervised_lokasi",
    )

    def to_domain(self) -> Lokasi:
        return Lokasi(
            id=self.id,
            name=self.name,
            latitude=self.latitude,
            longitude=self.longitude,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
