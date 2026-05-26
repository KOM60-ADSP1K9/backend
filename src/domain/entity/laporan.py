"""Domain model for laporan."""

from abc import ABC
from dataclasses import dataclass, field
import datetime
import enum
from typing import Self
from uuid import UUID, uuid4

from .barang import Barang
from .inquiry import ClaimInquiry, FoundInquiry, Inquiry, InquiryStatus


def _assert_date_not_future(value: datetime.date | None, field_name: str) -> None:
    if value is None:
        return
    today = datetime.datetime.now(datetime.timezone.utc).date()
    if value > today:
        raise ValueError(f"{field_name} cannot be in the future")


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
    inquiries: list[Inquiry] = field(default_factory=list)

    def __init__(
        self,
        id: UUID,
        type: LaporanType,
        status: LaporanStatus = LaporanStatus.DRAFT,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
        user_id: UUID | None = None,
        barang: Barang | None = None,
        inquiries: list[Inquiry] | None = None,
    ) -> None:
        self.id = id
        self.type = type
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.user_id = user_id
        self.barang = barang
        self.inquiries = list(inquiries) if inquiries is not None else []

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
        # allow re-activating from claim pending if claim is rejected
        # allow re-activating from found claim pending if claim is rejected
        if self.status not in {
            LaporanStatus.DRAFT,
            LaporanStatus.CLAIM_PENDING,
            LaporanStatus.FOUND_CLAIM_PENDING,
        }:
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

    def add_inquiry(self, inquiry: Inquiry) -> Inquiry:
        """Validate and append a new inquiry to this laporan's aggregate.

        Subclasses enforce inquiry-type compatibility via `_assert_inquiry_type_allowed`.
        Laporan must be in ACTIVE or its pending status (CLAIM_PENDING/FOUND_CLAIM_PENDING).
        Rejects if any inquiry already attached has status ACTIVE. When laporan is ACTIVE,
        transitions it to the pending status after appending.
        """
        pending_status = self._pending_status()
        if self.status not in {LaporanStatus.ACTIVE, pending_status}:
            raise ValueError(
                "Can only add inquiry to laporan with active or pending status"
            )

        if inquiry.sender_user_id == self.user_id:
            raise ValueError("Cannot add inquiry to your own laporan")

        self._assert_inquiry_type_allowed(inquiry)

        has_active = any(
            existing.status == InquiryStatus.ACTIVE for existing in self.inquiries
        )
        if has_active:
            raise ValueError(
                "Cannot add inquiry while there is an active inquiry for this laporan"
            )

        self.inquiries.append(inquiry)
        if self.status == LaporanStatus.ACTIVE:
            self._mark_pending()
        return inquiry

    def _assert_inquiry_type_allowed(self, inquiry: Inquiry) -> None:
        """Subclass hook: raise ValueError if `inquiry` type is not allowed."""
        raise NotImplementedError

    def _assert_inquiry_belongs(self, inquiry: Inquiry) -> None:
        if inquiry.laporan_id != self.id:
            raise ValueError("Inquiry does not belong to this laporan")

    def _pending_status(self) -> LaporanStatus:
        """Subclass hook: pending status used while inquiries are open."""
        raise NotImplementedError

    def _mark_pending(self) -> None:
        """Subclass hook: transition laporan into its pending status."""
        raise NotImplementedError

    def make_inquiry_active(self, inquiry: Inquiry) -> Inquiry:
        """Promote inquiry from PROPOSED to ACTIVE and transition laporan to IN_PROGRESS.

        Rejects if inquiry is not a valid type, does not belong to this laporan,
        is not in PROPOSED status, or another active inquiry already exists in
        this laporan's aggregate.
        """
        self._assert_inquiry_type_allowed(inquiry)
        self._assert_inquiry_belongs(inquiry)

        if inquiry.status != InquiryStatus.PROPOSED:
            raise ValueError("Can only activate inquiry from proposed status")

        has_other_active = any(
            existing.status == InquiryStatus.ACTIVE and existing.id != inquiry.id
            for existing in self.inquiries
        )
        if has_other_active:
            raise ValueError("There is already an active inquiry for this laporan")

        inquiry.status = InquiryStatus.ACTIVE
        self.mark_as_in_progress()
        return inquiry

    def reject_inquiry(self, inquiry: Inquiry) -> Inquiry:
        """Reject inquiry. Allowed from PROPOSED or ACTIVE.

        After rejection, laporan status is recomputed from remaining inquiries:
        - any ACTIVE remaining -> IN_PROGRESS
        - any PROPOSED remaining -> pending status (CLAIM_PENDING/FOUND_CLAIM_PENDING)
        - otherwise -> ACTIVE
        """
        self._assert_inquiry_type_allowed(inquiry)
        self._assert_inquiry_belongs(inquiry)

        if inquiry.status not in {
            InquiryStatus.PROPOSED,
            InquiryStatus.ACTIVE,
        }:
            raise ValueError("Can only reject inquiry from proposed or active status")

        inquiry.status = InquiryStatus.REJECTED

        has_active = any(
            existing.status == InquiryStatus.ACTIVE for existing in self.inquiries
        )
        has_proposed = any(
            existing.status == InquiryStatus.PROPOSED for existing in self.inquiries
        )
        if has_active:
            self.status = LaporanStatus.IN_PROGRESS
        elif has_proposed:
            self.status = self._pending_status()
        else:
            self.status = LaporanStatus.ACTIVE
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
        inquiries: list[Inquiry] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=LaporanType.HILANG,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            barang=barang,
            inquiries=inquiries,
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
        _assert_date_not_future(lost_at_date, "lost_at_date")
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
        _assert_date_not_future(lost_at_date, "lost_at_date")

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

    def _pending_status(self) -> LaporanStatus:
        return LaporanStatus.FOUND_CLAIM_PENDING

    def _mark_pending(self) -> None:
        self.mark_as_found_claim_pending()


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
        inquiries: list[Inquiry] | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=LaporanType.TEMUAN,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            user_id=user_id,
            barang=barang,
            inquiries=inquiries,
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
        _assert_date_not_future(found_at_date, "found_at_date")
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
        _assert_date_not_future(found_at_date, "found_at_date")

        self.found_at_location_id = found_at_location_id
        self.found_at_date = found_at_date

    def _assert_inquiry_type_allowed(self, inquiry: Inquiry) -> None:
        if not isinstance(inquiry, ClaimInquiry):
            raise ValueError("LaporanTemuan can only accept ClaimInquiry")

    def _pending_status(self) -> LaporanStatus:
        return LaporanStatus.CLAIM_PENDING

    def _mark_pending(self) -> None:
        self.mark_as_claim_pending()
