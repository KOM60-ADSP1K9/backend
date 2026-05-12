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

    def updateBarang(self, name: str, description: str, photo: str) -> None:
        """Update the attached barang child entity."""
        if self.barang is None:
            raise ValueError("Barang does not exist")

        self.assert_can_update()

        self.barang.update(
            name=name,
            description=description,
            photo=photo,
        )

    def assert_can_update(self) -> None:
        """Assert that the laporan can be updated. If not, throw an exception."""
        if self.status not in {
            LaporanStatus.DRAFT,
            LaporanStatus.ACTIVE,
        }:
            raise ValueError(
                "Cannot update laporan with status closed, self-resolved, claim pending, or resolved"
            )

    def resolve_status_update(self, newStatus: LaporanStatus) -> None:
        """Transition laporan status and call the appropriate mark_as_* method."""
        if newStatus == LaporanStatus.ACTIVE:
            self.mark_as_active()
        elif newStatus == LaporanStatus.CLAIM_PENDING:
            self.mark_as_claim_pending()
        elif newStatus == LaporanStatus.RESOLVED:
            self.mark_as_resolved()
        elif newStatus == LaporanStatus.SELF_RESOLVED:
            self.mark_as_self_resolved()
        else:
            raise ValueError(f"Invalid target status: {newStatus}")

    def mark_as_active(self) -> None:
        """Mark laporan as active and can be claimed or resolved."""
        if (
            self.status != LaporanStatus.DRAFT
            and self.status
            != LaporanStatus.CLAIM_PENDING  # allow re-activating from claim pending if claim is rejected
        ):
            raise ValueError(
                "Can only mark as active from draft or claim pending status"
            )

        self.status = LaporanStatus.ACTIVE

    def mark_as_claim_pending(self) -> None:
        """Mark laporan as claim pending (when there are user claims found report)."""
        if self.status != LaporanStatus.ACTIVE:
            raise ValueError("Can only mark as claim pending from active status")

        self.status = LaporanStatus.CLAIM_PENDING

    def mark_as_resolved(self) -> None:
        """Mark laporan as resolved (found goods back to the user, or lost goods is found)."""
        if (
            self.status != LaporanStatus.CLAIM_PENDING
            and self.status != LaporanStatus.ACTIVE
        ):
            raise ValueError(
                "Can only mark as resolved from active or claim pending status"
            )

        self.status = LaporanStatus.RESOLVED

    def mark_as_self_resolved(self) -> None:
        """Mark laporan as self-resolved (user that create the lost report has found the lost item)."""
        if self.status != LaporanStatus.ACTIVE:
            raise ValueError("Can only mark as self-resolved from active status")

        self.status = LaporanStatus.SELF_RESOLVED

    def mark_as_closed(self) -> None:
        """Mark laporan as closed (cancelled, wrong etc)."""
        if self.status != LaporanStatus.ACTIVE:
            raise ValueError("Can only mark as closed from active status")

        self.status = LaporanStatus.CLOSED


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

    def resolve_status_update(self, newStatus: LaporanStatus) -> None:
        """Transition laporan status and call the appropriate mark_as_* method."""
        if newStatus == LaporanStatus.ACTIVE:
            self.mark_as_active()
        elif newStatus == LaporanStatus.CLAIM_PENDING:
            raise ValueError("Cannot mark lost-item laporan as claim pending")
        elif newStatus == LaporanStatus.RESOLVED:
            self.mark_as_resolved()
        elif newStatus == LaporanStatus.SELF_RESOLVED:
            self.mark_as_self_resolved()
        else:
            raise ValueError(f"Invalid target status: {newStatus}")


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
