"""Usecase for creating lost reports."""

from datetime import date
from uuid import UUID

from src.application.i_storage_service import IStorageService
from src.core.exceptions import NotFoundException
from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.laporan import Laporan, LaporanHilang


class CreateLostReportRequest:
    def __init__(
        self,
        photo_content: bytes,
        photo_filename: str,
        lost_at_location_id: UUID,
        lost_at_date: date,
        user_id: UUID,
    ) -> None:
        self.photo_content = photo_content
        self.photo_filename = photo_filename
        self.lost_at_location_id = lost_at_location_id
        self.lost_at_date = lost_at_date
        self.user_id = user_id


class CreateLostReportResult:
    def __init__(self, laporan: Laporan) -> None:
        self.laporan = laporan


class CreateLostReportUsecase:
    """Create a new lost report for a mahasiswa."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        lokasi_repository: ILokasiRepository,
        storage_service: IStorageService,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._lokasi_repository = lokasi_repository
        self._storage_service = storage_service

    async def execute(self, request: CreateLostReportRequest) -> CreateLostReportResult:
        """Upload the photo stub and persist the new lost report."""
        lokasi = await self._lokasi_repository.find_by_id(request.lost_at_location_id)
        if lokasi is None:
            raise NotFoundException("Lokasi tidak ditemukan")

        photo_path = await self._storage_service.upload_photo(
            request.photo_content,
            request.photo_filename,
        )

        laporan = LaporanHilang.New(
            photo=photo_path,
            lost_at_location_id=request.lost_at_location_id,
            lost_at_date=request.lost_at_date,
            user_id=request.user_id,
        )

        saved_laporan = await self._laporan_repository.save(laporan)
        return CreateLostReportResult(laporan=saved_laporan)
