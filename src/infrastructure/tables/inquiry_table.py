"""Table that maps inquiry data."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base
from src.domain.entity.inquiry import (
    ClaimInquiry,
    FoundInquiry,
    Inquiry,
    InquiryStatus,
    InquiryType,
)
from src.infrastructure.tables.laporan_table import LaporanTable
from src.infrastructure.tables.user_table import UserTable


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class InquiryTable(Base):
    """Inquiry representation in the database."""

    __tablename__ = "inquiry"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    type: Mapped[InquiryType] = mapped_column(
        Enum(
            InquiryType,
            name="inquirytype",
            values_callable=_enum_values,
        ),
        nullable=False,
    )

    laporan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("laporan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    message_content: Mapped[str] = mapped_column(String, nullable=False)

    send_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    status: Mapped[InquiryStatus] = mapped_column(
        Enum(
            InquiryStatus,
            name="inquirystatus",
            values_callable=_enum_values,
        ),
        nullable=False,
        default=InquiryStatus.PROPOSED,
        server_default=InquiryStatus.PROPOSED.value,
    )

    # ClaimInquiry-only fields
    claimer_contact: Mapped[str | None] = mapped_column(String, nullable=True)
    proof_of_ownership: Mapped[str | None] = mapped_column(String, nullable=True)
    ktm: Mapped[str | None] = mapped_column(String, nullable=True)

    # FoundInquiry-only fields
    finder_contact: Mapped[str | None] = mapped_column(String, nullable=True)
    photo: Mapped[str | None] = mapped_column(String, nullable=True)

    laporan: Mapped[LaporanTable] = relationship(
        "LaporanTable",
        back_populates="inquiries",
        lazy="selectin",
    )

    sender: Mapped[UserTable] = relationship(
        "UserTable",
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
            (
                (type != InquiryType.CLAIM)
                | (
                    claimer_contact.is_not(None)
                    & proof_of_ownership.is_not(None)
                    & ktm.is_not(None)
                )
            )
            & (
                (type != InquiryType.CLAIM)
                | (finder_contact.is_(None) & photo.is_(None))
            )
            & (
                (type != InquiryType.FOUND)
                | (finder_contact.is_not(None) & photo.is_not(None))
            )
            & (
                (type != InquiryType.FOUND)
                | (
                    claimer_contact.is_(None)
                    & proof_of_ownership.is_(None)
                    & ktm.is_(None)
                )
            ),
            name="ck_inquiry_type_fields",
        ),
    )

    __mapper_args__ = {"polymorphic_on": type}

    def to_domain(self) -> Inquiry:
        if self.type == InquiryType.CLAIM:
            return ClaimInquiry(
                id=self.id,
                laporan_id=self.laporan_id,
                sender_user_id=self.sender_user_id,
                message_content=self.message_content,
                send_date=self.send_date,
                claimer_contact=self.claimer_contact or "",
                proof_of_ownership=self.proof_of_ownership or "",
                ktm=self.ktm or "",
                status=self.status,
                created_at=self.created_at,
                updated_at=self.updated_at,
            )

        if self.type == InquiryType.FOUND:
            return FoundInquiry(
                id=self.id,
                laporan_id=self.laporan_id,
                sender_user_id=self.sender_user_id,
                message_content=self.message_content,
                send_date=self.send_date,
                finder_contact=self.finder_contact or "",
                photo=self.photo or "",
                status=self.status,
                created_at=self.created_at,
                updated_at=self.updated_at,
            )

        raise ValueError(f"Unsupported inquiry type: {self.type}")

    @classmethod
    def from_domain(cls, inquiry: Inquiry) -> "InquiryTable":
        """Convert a domain model to the mapped table model."""
        if isinstance(inquiry, ClaimInquiry) or inquiry.type == InquiryType.CLAIM:
            return ClaimInquiryTable(
                id=inquiry.id,
                type=InquiryType.CLAIM,
                laporan_id=inquiry.laporan_id,
                sender_user_id=inquiry.sender_user_id,
                message_content=inquiry.message_content,
                send_date=inquiry.send_date,
                claimer_contact=getattr(inquiry, "claimer_contact", None),
                proof_of_ownership=getattr(inquiry, "proof_of_ownership", None),
                ktm=getattr(inquiry, "ktm", None),
                status=getattr(inquiry, "status", InquiryStatus.PROPOSED),
                created_at=inquiry.created_at,
                updated_at=inquiry.updated_at,
            )

        if isinstance(inquiry, FoundInquiry) or inquiry.type == InquiryType.FOUND:
            return FoundInquiryTable(
                id=inquiry.id,
                type=InquiryType.FOUND,
                laporan_id=inquiry.laporan_id,
                sender_user_id=inquiry.sender_user_id,
                message_content=inquiry.message_content,
                send_date=inquiry.send_date,
                finder_contact=getattr(inquiry, "finder_contact", None),
                photo=getattr(inquiry, "photo", None),
                status=getattr(inquiry, "status", InquiryStatus.PROPOSED),
                created_at=inquiry.created_at,
                updated_at=inquiry.updated_at,
            )

        raise ValueError(f"Unsupported inquiry type: {inquiry.type}")


class ClaimInquiryTable(InquiryTable):
    """Single-table inheritance row for claim inquiry."""

    __mapper_args__ = {"polymorphic_identity": InquiryType.CLAIM}


class FoundInquiryTable(InquiryTable):
    """Single-table inheritance row for found inquiry."""

    __mapper_args__ = {"polymorphic_identity": InquiryType.FOUND}
