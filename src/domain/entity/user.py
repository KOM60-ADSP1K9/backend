"""
Domain model for user
"""

import enum
import datetime
from typing import Self
from uuid import UUID, uuid4

ALLOWED_EMAIL_DOMAIN = "@apps.ipb.ac.id"


class UserRole(str, enum.Enum):
    MAHASISWA = "MAHASISWA"
    STAFF = "STAFF"


class User:
    """User domain model"""

    @classmethod
    def register(
        cls,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.MAHASISWA,
        nim: str | None = None,
        fakultas: str | None = None,
        departemen: str | None = None,
        nip: str | None = None,
    ) -> Self:
        """Register a new user with domain validation."""
        if not email.endswith(ALLOWED_EMAIL_DOMAIN):
            raise ValueError(f"Hanya {ALLOWED_EMAIL_DOMAIN} email yang diperbolehkan")

        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            email=email,
            hashed_password=hashed_password,
            role=role,
            nim=nim,
            fakultas=fakultas,
            departemen=departemen,
            nip=nip,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )

    def __init__(
        self,
        id: UUID,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.MAHASISWA,
        nim: str | None = None,
        fakultas: str | None = None,
        departemen: str | None = None,
        nip: str | None = None,
        email_verified_at: datetime.datetime | None = None,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        self.id = id
        self.email = email
        self.hashed_password = hashed_password
        self.role = role
        self.nim = nim
        self.fakultas = fakultas
        self.departemen = departemen
        self.nip = nip
        self.email_verified_at = email_verified_at
        self.created_at = created_at
        self.updated_at = updated_at

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    def verify_email(self) -> None:
        """Mark the email as verified."""
        self.email_verified_at = datetime.datetime.now(datetime.timezone.utc)
        self.updated_at = self.email_verified_at
