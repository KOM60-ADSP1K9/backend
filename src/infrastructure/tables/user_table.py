"""
Table that map to User domain model.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.db import Base
from src.domain.entity.user import Mahasiswa, Staff, User, UserRole


from src.infrastructure.tables.lokasi_table import LokasiTable


class UserTable(Base):
    """
    User representation in the database.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"),
        nullable=False,
        default=UserRole.MAHASISWA,
        server_default=UserRole.MAHASISWA.value,
    )

    nim: Mapped[str | None] = mapped_column(String, nullable=True)

    fakultas: Mapped[str | None] = mapped_column(String, nullable=True)

    departemen: Mapped[str | None] = mapped_column(String, nullable=True)

    nip: Mapped[str | None] = mapped_column(String, nullable=True)

    lokasi_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lokasi.id", ondelete="SET NULL"),
        nullable=True,
    )

    supervised_lokasi: Mapped["LokasiTable | None"] = relationship(
        "LokasiTable",
        back_populates="supervisors",
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
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

    def to_user(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            hashed_password=self.hashed_password,
            role=self.role,
            nim=self.nim,
            fakultas=self.fakultas,
            departemen=self.departemen,
            nip=self.nip,
            lokasi_id=self.lokasi_id,
            email_verified_at=self.email_verified_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_staff(self) -> Staff:
        return Staff(
            id=self.id,
            email=self.email,
            hashed_password=self.hashed_password,
            nip=self.nip,
            nim=self.nim,
            fakultas=self.fakultas,
            departemen=self.departemen,
            lokasi_id=self.lokasi_id,
            email_verified_at=self.email_verified_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_mahasiswa(self) -> Mahasiswa:
        return Mahasiswa(
            id=self.id,
            email=self.email,
            hashed_password=self.hashed_password,
            nim=self.nim,
            fakultas=self.fakultas,
            departemen=self.departemen,
            nip=self.nip,
            lokasi_id=self.lokasi_id,
            email_verified_at=self.email_verified_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, user: User) -> "UserTable":
        """Convert domain model to table model"""
        return cls(
            id=user.id,
            email=user.email,
            hashed_password=user.hashed_password,
            role=user.role,
            nim=user.nim,
            fakultas=user.fakultas,
            departemen=user.departemen,
            nip=user.nip,
            lokasi_id=user.lokasi_id,
            email_verified_at=user.email_verified_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
