"""Usecase: Get all laporan for the homepage."""

from collections.abc import Iterable

from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.laporan import Laporan


class GetAllLaporanResult:
    def __init__(self, laporan: Iterable[Laporan]) -> None:
        self.laporan = laporan


class GetAllLaporanUsecase:
    """Get-all-laporan use case with injected repository."""

    def __init__(self, laporan_repository: ILaporanRepository) -> None:
        self._laporan_repository = laporan_repository

    async def execute(self) -> GetAllLaporanResult:
        """Return every laporan in the system."""
        laporan = await self._laporan_repository.findAll()
        return GetAllLaporanResult(laporan=laporan)
