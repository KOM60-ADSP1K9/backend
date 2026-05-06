"""Domain model for laporan."""

from abc import ABC
from dataclasses import dataclass
import datetime
import enum
from typing import Self
from uuid import UUID, uuid4

from .barang import Barang


class LaporanType(str, enum.Enum):
    """HILANG OR TEMUAN."""

    HILANG = "hilang"
    TEMUAN = "temuan"


class LaporanStatus(str, enum.Enum):
    """Lifecycle states for laporan."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLAIM_PENDING = "claim pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    SELF_RESOLVED = "self-resolved"


@dataclass
class Laporan(ABC):
    """Base laporan domain model."""

    id: UUID
    type: LaporanType
    status: LaporanStatus
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None
    user_id: UUID | None = None
    barang: Barang | None = None

    def __init__(
        self,
        id: UUID,
        type: LaporanType,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
        user_id: UUID | None = None,
        barang: Barang | None = None,
    ) -> None:
        self.id = id
        self.type = type
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.user_id = user_id
        self.barang = barang

    def addBarang(self, barang: Barang) -> None:
        """Attach the barang child entity to this laporan."""
        if self.barang is not None:
            raise ValueError("Barang already exists")

        self.assert_can_update()

        self.barang = barang

    def updateBarang(self, barang: Barang) -> None:
        """Update the attached barang child entity."""
        if self.barang is None:
            raise ValueError("Barang does not exist")

        self.assert_can_update()

        self.barang.update(
            name=barang.name,
            description=barang.description,
            photo=barang.photo,
        )

    def assert_can_update(self) -> None:
        """Assert that the laporan can be updated. If not, throw an exception."""
        if self.status in {
            LaporanStatus.CLOSED,
            LaporanStatus.SELF_RESOLVED,
            LaporanStatus.CLAIM_PENDING,
            LaporanStatus.RESOLVED,
        }:
            raise ValueError(
                "Cannot update laporan with status closed, self-resolved, claim pending, or resolved"
            )


@dataclass
class LaporanHilang(Laporan):
    """Concrete laporan for lost items."""

    lost_at_location_id: UUID | None = None
    lost_at_date: datetime.date | None = None

    def __init__(
        self,
        id: UUID,
        lost_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
        lost_at_date: datetime.date | None = None,
        user_id: UUID | None = None,
        barang: Barang | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=LaporanType.HILANG,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            barang=barang,
        )
        self.lost_at_location_id = lost_at_location_id
        self.lost_at_date = lost_at_date

    @property
    def lostAtLocation(self) -> UUID | None:
        return self.lost_at_location_id

    @lostAtLocation.setter
    def lostAtLocation(self, value: UUID | None) -> None:
        self.lost_at_location_id = value

    @classmethod
    def New(
        cls,
        lost_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        lost_at_date: datetime.date | None = None,
        user_id: UUID | None = None,
        barang: Barang | None = None,
    ) -> Self:
        """Create a new lost-item laporan."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            lost_at_location_id=lost_at_location_id,
            status=status,
            created_at=now,
            updated_at=now,
            lost_at_date=lost_at_date,
            user_id=user_id,
            barang=barang,
        )


@dataclass
class LaporanTemuan(Laporan):
    """Concrete laporan for found items."""

    found_at_location_id: UUID | None = None
    found_at_date: datetime.date | None = None

    def __init__(
        self,
        id: UUID,
        found_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
        found_at_date: datetime.date | None = None,
        user_id: UUID | None = None,
        barang: Barang | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=LaporanType.TEMUAN,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            barang=barang,
        )
        self.found_at_location_id = found_at_location_id
        self.found_at_date = found_at_date

    @property
    def foundAtLocation(self) -> UUID | None:
        return self.found_at_location_id

    @foundAtLocation.setter
    def foundAtLocation(self, value: UUID | None) -> None:
        self.found_at_location_id = value

    @classmethod
    def New(
        cls,
        found_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        found_at_date: datetime.date | None = None,
        user_id: UUID | None = None,
        barang: Barang | None = None,
    ) -> Self:
        """Create a new found-item laporan."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            found_at_location_id=found_at_location_id,
            status=status,
            created_at=now,
            updated_at=now,
            found_at_date=found_at_date,
            user_id=user_id,
            barang=barang,
        )
