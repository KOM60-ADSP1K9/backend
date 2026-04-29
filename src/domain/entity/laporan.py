"""Domain model for laporan."""

from abc import ABC
from dataclasses import dataclass
import datetime
import enum
from typing import Self
from uuid import UUID, uuid4


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
    photo: str
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    def __init__(
        self,
        id: UUID,
        type: LaporanType,
        photo: str,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        self.id = id
        self.type = type
        self.status = status
        self.photo = photo
        self.created_at = created_at
        self.updated_at = updated_at


@dataclass
class LaporanHilang(Laporan):
    """Concrete laporan for lost items."""

    lost_at_location_id: UUID | None = None
    lost_at_date: datetime.date | None = None

    def __init__(
        self,
        id: UUID,
        photo: str,
        lost_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
        lost_at_date: datetime.date | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=LaporanType.HILANG,
            photo=photo,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
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
        photo: str,
        lost_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        lost_at_date: datetime.date | None = None,
    ) -> Self:
        """Create a new lost-item laporan."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            photo=photo,
            lost_at_location_id=lost_at_location_id,
            status=status,
            created_at=now,
            updated_at=now,
            lost_at_date=lost_at_date,
        )


@dataclass
class LaporanTemuan(Laporan):
    """Concrete laporan for found items."""

    found_at_location_id: UUID | None = None
    found_at_date: datetime.date | None = None

    def __init__(
        self,
        id: UUID,
        photo: str,
        found_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
        found_at_date: datetime.date | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=LaporanType.TEMUAN,
            photo=photo,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
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
        photo: str,
        found_at_location_id: UUID | None = None,
        status: LaporanStatus = LaporanStatus.DRAFT,
        found_at_date: datetime.date | None = None,
    ) -> Self:
        """Create a new found-item laporan."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            photo=photo,
            found_at_location_id=found_at_location_id,
            status=status,
            created_at=now,
            updated_at=now,
            found_at_date=found_at_date,
        )
