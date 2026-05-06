"""Stub storage service used until real object storage is available."""

from src.application.i_storage_service import IStorageService


class StubStorageService(IStorageService):
    """Temporary storage implementation that returns a deterministic path."""

    async def upload_photo(self, content: bytes, filename: str) -> str:
        return f"https://placehold.co/600x400?text=stub://lost-reports/{filename}"
