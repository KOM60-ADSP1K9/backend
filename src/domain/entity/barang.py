"""Domain model for barang."""

from dataclasses import dataclass
import datetime
from typing import ClassVar, Self
from uuid import UUID, uuid4


@dataclass
class Barang:
    """Barang child entity."""

    id: UUID
    name: str
    description: str
    photo: str
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None

    MAX_PHOTO_SIZE_MB: ClassVar[int] = 5
    ALLOWED_PHOTO_TYPES: ClassVar[tuple[str, str]] = ("image/jpeg", "image/png")

    def __init__(
        self,
        id: UUID,
        name: str,
        description: str,
        photo: str,
        created_at: datetime.datetime | None = None,
        updated_at: datetime.datetime | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.photo = photo
        self.created_at = created_at
        self.updated_at = updated_at

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        photo: str | None = None,
    ) -> None:
        """Update the barang attributes."""
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if photo is not None:
            self.photo = photo
        self.updated_at = datetime.datetime.now(datetime.timezone.utc)

    @classmethod
    def New(
        cls,
        name: str,
        description: str,
        photo: str,
    ) -> Self:
        """Create a new barang."""
        now = datetime.datetime.now(datetime.timezone.utc)
        return cls(
            id=uuid4(),
            name=name,
            description=description,
            photo=photo,
            created_at=now,
            updated_at=now,
        )
