"""Domain model for lokasi."""

from datetime import datetime
from dataclasses import dataclass
from uuid import UUID


@dataclass
class Lokasi:
    """Lokasi domain model."""

    id: UUID
    name: str
    latitude: float
    longitude: float
    created_at: datetime | None = None
    updated_at: datetime | None = None
