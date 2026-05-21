"""Domain model for laporan."""

from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass
import datetime
import enum
from typing import Self
from uuid import UUID, uuid4

from .barang import Barang
from .inquiry import ClaimInquiry, FoundInquiry, Inquiry, InquiryStatus


class LaporanType(str, enum.Enum):
    """HILANG OR TEMUAN."""

    HILANG = "hilang"
    TEMUAN = "temuan"


class LaporanStatus(str, enum.Enum):
    """Lifecycle states for laporan."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLAIM_PENDING = "claim pending"
    FOUND_CLAIM_PENDING = "found claim pending"
    IN_PROGRESS = "in progress"
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

    def assert_can_update(self) -> None:
        """Assert that the laporan can be updated. If not, throw an exception."""
        if self.status not in {
            LaporanStatus.DRAFT,
            LaporanStatus.ACTIVE,
        }:
            raise ValueError(
                "Cannot update laporan with status closed, self-resolved, claim pending, or resolved"
            )

    def assert_can_delete(self) -> None:
        """Assert that the laporan can be deleted. If not, throw an exception."""
        if self.status not in {LaporanStatus.DRAFT, LaporanStatus.ACTIVE}:
            raise ValueError("Can only delete laporan with draft status")

    def addBarang(self, barang: Barang) -> None:
        """Attach the barang child entity to this laporan."""
        if self.barang is not None:
            raise ValueError("Barang already exists")

        self.assert_can_update()

        self.barang = barang

    def updateBarang(
        self,
        name: str,
        description: str,
        photo: str,
        kategori_barang_id: UUID,
    ) -> None:
        """Update the attached barang child entity."""
        if self.barang is None:
            raise ValueError("Barang does not exist")

        self.assert_can_update()

        self.barang.update(
            name=name,
            description=description,
            photo=photo,
            kategori_barang_id=kategori_barang_id,
        )

    def resolve_status_update(self, newStatus: LaporanStatus) -> None:
        """Transition laporan status and call the appropriate mark_as_* method."""
        if newStatus == LaporanStatus.ACTIVE:
            self.mark_as_active()
        elif newStatus == LaporanStatus.CLAIM_PENDING:
            self.mark_as_claim_pending()
        elif newStatus == LaporanStatus.IN_PROGRESS:
            self.mark_as_in_progress()
        elif newStatus == LaporanStatus.RESOLVED:
            self.mark_as_resolved()
        elif newStatus == LaporanStatus.SELF_RESOLVED:
            self.mark_as_self_resolved()
        else:
            raise ValueError(f"Invalid target status: {newStatus}")

    def mark_as_active(self) -> None:
        """Mark laporan as active and can be claimed or resolved."""
        if (
            self.status
            not in {
                LaporanStatus.DRAFT,
                LaporanStatus.CLAIM_PENDING,  # allow re-activating from claim pending if claim is rejected
                LaporanStatus.FOUND_CLAIM_PENDING,  # allow re-activating from found claim pending if claim is rejected
            }
        ):
            raise ValueError(
                "Can only mark as active from draft, claim pending, or found claim pending status"
            )

        self.status = LaporanStatus.ACTIVE

    def mark_as_claim_pending(self) -> None:
        """Mark laporan as claim pending (when there are user claims found report)."""
        if self.status != LaporanStatus.ACTIVE:
            raise ValueError("Can only mark as claim pending from active status")

        self.status = LaporanStatus.CLAIM_PENDING

    def mark_as_found_claim_pending(self) -> None:
        """Mark laporan as found claim pending (lost item reported found by someone, awaiting claim)."""
        if self.status != LaporanStatus.ACTIVE:
            raise ValueError("Can only mark as found claim pending from active status")

        self.status = LaporanStatus.FOUND_CLAIM_PENDING

    def mark_as_in_progress(self) -> None:
        """Mark laporan as in progress (claim accepted, handover in progress)."""
        if self.status != LaporanStatus.CLAIM_PENDING:
            raise ValueError("Can only mark as in progress from claim pending status")

        self.status = LaporanStatus.IN_PROGRESS

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

    def add_inquiry(
        self,
        inquiry: Inquiry,
        existing_inquiries: Iterable[Inquiry],
    ) -> Inquiry:
        """Validate and accept a new inquiry for this laporan.

        Subclasses enforce inquiry-type compatibility via `_assert_inquiry_type_allowed`.
        Laporan must be in ACTIVE status. Rejects if any existing inquiry has status ACTIVE.
        """
        if self.status != LaporanStatus.ACTIVE:
            raise ValueError("Can only add inquiry to laporan with active status")

        self._assert_inquiry_type_allowed(inquiry)

        has_active = any(
            existing.status == InquiryStatus.ACTIVE for existing in existing_inquiries
        )
        if has_active:
            raise ValueError(
                "Cannot add inquiry while there is an active inquiry for this laporan"
            )

        return inquiry

    def _assert_inquiry_type_allowed(self, inquiry: Inquiry) -> None:
        """Subclass hook: raise ValueError if `inquiry` type is not allowed."""
        raise NotImplementedError

    def _assert_inquiry_belongs(self, inquiry: Inquiry) -> None:
        if inquiry.laporan_id != self.id:
            raise ValueError("Inquiry does not belong to this laporan")

    def make_inquiry_active(
        self,
        inquiry: Inquiry,
        existing_inquiries: Iterable[Inquiry],
    ) -> Inquiry:
        """Promote inquiry from PROPOSED to ACTIVE.

        Rejects if inquiry is not a valid type, does not belong to this laporan,
        is not in PROPOSED status, or another active inquiry already exists.
        """
        self._assert_inquiry_type_allowed(inquiry)
        self._assert_inquiry_belongs(inquiry)

        if inquiry.status != InquiryStatus.PROPOSED:
            raise ValueError("Can only activate inquiry from proposed status")

        has_other_active = any(
            existing.status == InquiryStatus.ACTIVE and existing.id != inquiry.id
            for existing in existing_inquiries
        )
        if has_other_active:
            raise ValueError("There is already an active inquiry for this laporan")

        inquiry.status = InquiryStatus.ACTIVE
        return inquiry

    def reject_inquiry(self, inquiry: Inquiry) -> Inquiry:
        """Reject inquiry. Allowed from PROPOSED or ACTIVE."""
        self._assert_inquiry_type_allowed(inquiry)
        self._assert_inquiry_belongs(inquiry)

        if inquiry.status not in {
            InquiryStatus.PROPOSED,
            InquiryStatus.ACTIVE,
        }:
            raise ValueError("Can only reject inquiry from proposed or active status")

        inquiry.status = InquiryStatus.REJECTED
        return inquiry


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

    def update(
        self, lost_at_location_id: UUID | None, lost_at_date: datetime.date | None
    ) -> None:
        """Update laporan hilang details."""
        self.assert_can_update()

        self.lost_at_location_id = lost_at_location_id
        self.lost_at_date = lost_at_date

    def resolve_status_update(self, newStatus: LaporanStatus) -> None:
        """Transition laporan status and call the appropriate mark_as_* method."""
        if newStatus == LaporanStatus.ACTIVE:
            self.mark_as_active()
        elif newStatus == LaporanStatus.CLAIM_PENDING:
            raise ValueError("Cannot mark lost-item laporan as claim pending")
        elif newStatus == LaporanStatus.FOUND_CLAIM_PENDING:
            self.mark_as_found_claim_pending()
        elif newStatus == LaporanStatus.IN_PROGRESS:
            self.mark_as_in_progress()
        elif newStatus == LaporanStatus.RESOLVED:
            self.mark_as_resolved()
        elif newStatus == LaporanStatus.SELF_RESOLVED:
            self.mark_as_self_resolved()
        else:
            raise ValueError(f"Invalid target status: {newStatus}")

    def mark_as_in_progress(self) -> None:
        """Mark lost-item laporan as in progress (only from found claim pending)."""
        if self.status != LaporanStatus.FOUND_CLAIM_PENDING:
            raise ValueError(
                "Can only mark lost-item laporan as in progress from found claim pending status"
            )

        self.status = LaporanStatus.IN_PROGRESS

    def _assert_inquiry_type_allowed(self, inquiry: Inquiry) -> None:
        if not isinstance(inquiry, FoundInquiry):
            raise ValueError("LaporanHilang can only accept FoundInquiry")


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

    def update(
        self, found_at_location_id: UUID | None, found_at_date: datetime.date | None
    ) -> None:
        """Update laporan temuan details."""
        self.assert_can_update()

        self.found_at_location_id = found_at_location_id
        self.found_at_date = found_at_date

    def _assert_inquiry_type_allowed(self, inquiry: Inquiry) -> None:
        if not isinstance(inquiry, ClaimInquiry):
            raise ValueError("LaporanTemuan can only accept ClaimInquiry")
