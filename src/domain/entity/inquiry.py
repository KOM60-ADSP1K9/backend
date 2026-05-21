"""Domain model for inquiry."""

from abc import ABC
from dataclasses import dataclass
import datetime
import enum
from typing import Self
from uuid import UUID, uuid4


class InquiryType(str, enum.Enum):
    """Type of inquiry."""

    CLAIM = "claim"
    FOUND = "found"


class InquiryStatus(str, enum.Enum):
    """Lifecycle states for inquiry."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    REJECTED = "rejected"


@dataclass
class Inquiry(ABC):
    """Base inquiry domain model."""

    id: UUID
    type: InquiryType
    laporan_id: UUID
    sender_user_id: UUID
    message_content: str
    send_date: datetime.datetime
    status: InquiryStatus = InquiryStatus.PROPOSED
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    def __init__(
        self,
        id: UUID,
        type: InquiryType,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        send_date: datetime.datetime,
        status: InquiryStatus = InquiryStatus.PROPOSED,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        self.id = id
        self.type = type
        self.laporan_id = laporan_id
        self.sender_user_id = sender_user_id
        self.message_content = message_content
        self.send_date = send_date
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at


@dataclass
class ClaimInquiry(Inquiry):
    """Concrete inquiry for claiming a found laporan (LaporanTemuan)."""

    claimer_contact: str | None = None
    proof_of_ownership: str | None = None
    ktm: str | None = None

    def __init__(
        self,
        id: UUID,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        send_date: datetime.datetime,
        claimer_contact: str,
        proof_of_ownership: str,
        ktm: str,
        status: InquiryStatus = InquiryStatus.PROPOSED,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=InquiryType.CLAIM,
            laporan_id=laporan_id,
            sender_user_id=sender_user_id,
            message_content=message_content,
            send_date=send_date,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )
        self.claimer_contact = claimer_contact
        self.proof_of_ownership = proof_of_ownership
        self.ktm = ktm

    @classmethod
    def New(
        cls,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        claimer_contact: str,
        proof_of_ownership: str,
        ktm: str,
    ) -> Self:
        """Create a new claim inquiry."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            laporan_id=laporan_id,
            sender_user_id=sender_user_id,
            message_content=message_content,
            send_date=now,
            claimer_contact=claimer_contact,
            proof_of_ownership=proof_of_ownership,
            ktm=ktm,
            created_at=now,
            updated_at=now,
        )


@dataclass
class FoundInquiry(Inquiry):
    """Concrete inquiry for reporting a found item against a LaporanHilang."""

    finder_contact: str | None = None
    photo: str | None = None

    def __init__(
        self,
        id: UUID,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        send_date: datetime.datetime,
        finder_contact: str,
        photo: str,
        status: InquiryStatus = InquiryStatus.PROPOSED,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        super().__init__(
            id=id,
            type=InquiryType.FOUND,
            laporan_id=laporan_id,
            sender_user_id=sender_user_id,
            message_content=message_content,
            send_date=send_date,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )
        self.finder_contact = finder_contact
        self.photo = photo

    @classmethod
    def New(
        cls,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        finder_contact: str,
        photo: str,
    ) -> Self:
        """Create a new found inquiry."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            laporan_id=laporan_id,
            sender_user_id=sender_user_id,
            message_content=message_content,
            send_date=now,
            finder_contact=finder_contact,
            photo=photo,
            created_at=now,
            updated_at=now,
        )
