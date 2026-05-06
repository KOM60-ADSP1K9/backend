"""Table that maps laporan data."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.domain.entity.laporan import (
    Laporan,
    LaporanHilang,
    LaporanStatus,
    LaporanTemuan,
    LaporanType,
)
from src.infrastructure.tables.barang_table import BarangTable
from src.infrastructure.tables.user_table import UserTable


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class LaporanTable(Base):
    """Laporan representation in the database."""

    __tablename__ = "laporan"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    type: Mapped[LaporanType] = mapped_column(
        Enum(
            LaporanType,
            name="laporantype",
            values_callable=_enum_values,
        ),
        nullable=False,
    )

    status: Mapped[LaporanStatus] = mapped_column(
        Enum(
            LaporanStatus,
            name="laporanstatus",
            values_callable=_enum_values,
        ),
        nullable=False,
        default=LaporanStatus.DRAFT,
        server_default=LaporanStatus.DRAFT.value,
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped[UserTable | None] = relationship(
        "UserTable",
        lazy="selectin",
    )

    lost_at_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lokasi.id", ondelete="SET NULL"),
        nullable=True,
    )

    lost_at_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    found_at_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lokasi.id", ondelete="SET NULL"),
        nullable=True,
    )

    found_at_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    barang: Mapped[BarangTable | None] = relationship(
        "BarangTable",
        back_populates="laporan",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="selectin",
    )

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

    __table_args__ = (
        CheckConstraint(
            ((type != LaporanType.HILANG) | found_at_location_id.is_(None))
            & ((type != LaporanType.HILANG) | found_at_date.is_(None))
            & ((type != LaporanType.TEMUAN) | lost_at_location_id.is_(None))
            & ((type != LaporanType.TEMUAN) | lost_at_date.is_(None)),
            name="ck_laporan_type_location",
        ),
    )

    __mapper_args__ = {"polymorphic_on": type}

    def to_domain(self) -> Laporan:
        if self.type == LaporanType.HILANG:
            laporan = LaporanHilang(
                id=self.id,
                lost_at_location_id=self.lost_at_location_id,
                status=self.status,
                created_at=self.created_at,
                updated_at=self.updated_at,
                lost_at_date=self.lost_at_date,
                user_id=self.user_id,
                barang=self.barang.to_domain() if self.barang is not None else None,
            )
            return laporan

        if self.type == LaporanType.TEMUAN:
            laporan = LaporanTemuan(
                id=self.id,
                found_at_location_id=self.found_at_location_id,
                status=self.status,
                created_at=self.created_at,
                updated_at=self.updated_at,
                found_at_date=self.found_at_date,
                user_id=self.user_id,
                barang=self.barang.to_domain() if self.barang is not None else None,
            )
            return laporan

        raise ValueError(f"Unsupported laporan type: {self.type}")

    @classmethod
    def from_domain(cls, laporan: Laporan) -> "LaporanTable":
        """Convert a domain model to the mapped table model."""
        if isinstance(laporan, LaporanHilang) or laporan.type == LaporanType.HILANG:
            row = LaporanHilangTable(
                id=laporan.id,
                type=LaporanType.HILANG,
                status=laporan.status,
                user_id=laporan.user_id,
                lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
                lost_at_date=getattr(laporan, "lost_at_date", None),
                created_at=laporan.created_at,
                updated_at=laporan.updated_at,
            )
            if laporan.barang is not None:
                row.barang = BarangTable.from_domain(laporan.barang, laporan.id)
            return row

        if isinstance(laporan, LaporanTemuan) or laporan.type == LaporanType.TEMUAN:
            row = LaporanTemuanTable(
                id=laporan.id,
                type=LaporanType.TEMUAN,
                status=laporan.status,
                user_id=laporan.user_id,
                found_at_location_id=getattr(laporan, "found_at_location_id", None),
                found_at_date=getattr(laporan, "found_at_date", None),
                created_at=laporan.created_at,
                updated_at=laporan.updated_at,
            )
            if laporan.barang is not None:
                row.barang = BarangTable.from_domain(laporan.barang, laporan.id)
            return row

        raise ValueError(f"Unsupported laporan type: {laporan.type}")


class LaporanHilangTable(LaporanTable):
    """Single-table inheritance row for laporan hilang."""

    __mapper_args__ = {"polymorphic_identity": LaporanType.HILANG}


class LaporanTemuanTable(LaporanTable):
    """Single-table inheritance row for laporan temuan."""

    __mapper_args__ = {"polymorphic_identity": LaporanType.TEMUAN}
