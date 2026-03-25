"""Domain model for lokasi."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class Lokasi:
    """Lokasi domain model."""

    id: UUID
    name: str
    latitude: float
    longitude: float
