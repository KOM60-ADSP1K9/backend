"""Usecase: Get all lokasi."""

from collections.abc import Iterable

from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.domain.entity.lokasi import Lokasi


class GetAllLokasiResult:
    def __init__(self, lokasi: Iterable[Lokasi]) -> None:
        self.lokasi = lokasi


class GetAllLokasiUsecase:
    """Get-all-lokasi use case with injected repository."""

    def __init__(self, lokasi_repository: ILokasiRepository) -> None:
        self._lokasi_repository = lokasi_repository

    async def execute(self) -> GetAllLokasiResult:
        """Return every lokasi in the system."""
        lokasi = await self._lokasi_repository.get_all()
        return GetAllLokasiResult(lokasi=lokasi)
