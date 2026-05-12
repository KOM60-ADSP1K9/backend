"""Stub storage service used until real object storage is available."""

from src.application.i_storage_service import IStorageService


class StubStorageService(IStorageService):
    """Temporary storage implementation that returns a deterministic path."""

    def __init__(self) -> None:
        self.deleted_urls: list[str] = []

    async def upload_photo(self, content: bytes, filename: str) -> str:
        return f"https://placehold.co/600x400?text=stub://lost-reports/{''.join(filename.split())}"

    async def delete_photo(self, photo_url: str) -> None:
        self.deleted_urls.append(photo_url)
