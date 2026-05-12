"""Abstract interface for storage operations."""

from abc import ABC, abstractmethod


class IStorageService(ABC):
    """Port for storing uploaded files."""

    @abstractmethod
    async def upload_photo(self, content: bytes, filename: str) -> str:
        """Store a photo and return its storage reference."""

    @abstractmethod
    async def delete_photo(self, photo_url: str) -> None:
        """Delete a previously uploaded photo by its storage reference."""
