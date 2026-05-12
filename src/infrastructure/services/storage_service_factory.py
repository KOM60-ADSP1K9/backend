"""Factory for selecting the IStorageService implementation at runtime."""

from src.application.i_storage_service import IStorageService
from src.core.config import Settings, settings as default_settings
from src.infrastructure.services.r2_storage_service import R2StorageService
from src.infrastructure.services.stub_storage_service import StubStorageService


def create_storage_service(settings: Settings = default_settings) -> IStorageService:
    """Return the IStorageService implementation selected by FACTORY_STORAGE_TYPE."""
    storage_type = settings.FACTORY_STORAGE_TYPE

    if storage_type == "r2":
        return R2StorageService(settings=settings)

    if storage_type in ("", "stub"):
        return StubStorageService()

    raise ValueError(
        f"Unsupported FACTORY_STORAGE_TYPE: {storage_type!r}. Expected 'r2' or 'stub'."
    )
