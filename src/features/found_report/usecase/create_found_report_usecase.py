"""Usecase for creating found reports."""

from datetime import date
from uuid import UUID

from src.application.i_storage_service import IStorageService
from src.core.exceptions import NotFoundException
from src.domain.entity.barang import Barang
from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanTemuan


class CreateFoundReportRequest:
    def __init__(
        self,
        photo_content: bytes,
        photo_filename: str,
        barang_name: str,
        barang_description: str,
        found_at_location_id: UUID,
        found_at_date: date,
        user_id: UUID,
    ) -> None:
        self.photo_content = photo_content
        self.photo_filename = photo_filename
        self.barang_name = barang_name
        self.barang_description = barang_description
        self.found_at_location_id = found_at_location_id
        self.found_at_date = found_at_date
        self.user_id = user_id


class CreateFoundReportResult:
    def __init__(self, laporan: Laporan) -> None:
        self.laporan = laporan


class CreateFoundReportUsecase:
    """Create a new found report for an authenticated user."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        lokasi_repository: ILokasiRepository,
        storage_service: IStorageService,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._lokasi_repository = lokasi_repository
        self._storage_service = storage_service

    async def execute(
        self, request: CreateFoundReportRequest
    ) -> CreateFoundReportResult:
        """Upload the barang photo and persist the new found report."""
        lokasi = await self._lokasi_repository.find_by_id(request.found_at_location_id)
        if lokasi is None:
            raise NotFoundException("Lokasi tidak ditemukan")

        photo_path = await self._storage_service.upload_photo(
            request.photo_content,
            request.photo_filename,
        )

        barang = Barang.New(
            name=request.barang_name,
            description=request.barang_description,
            photo=photo_path,
        )

        laporan = LaporanTemuan.New(
            found_at_location_id=request.found_at_location_id,
            found_at_date=request.found_at_date,
            user_id=request.user_id,
            status=LaporanStatus.ACTIVE,
        )
        laporan.addBarang(barang)

        saved_laporan = await self._laporan_repository.save(laporan)
        return CreateFoundReportResult(laporan=saved_laporan)
