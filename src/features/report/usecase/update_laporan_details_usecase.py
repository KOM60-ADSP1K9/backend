"""Usecase for updating laporan details (location and date)."""

from datetime import date
from uuid import UUID

from src.core.exceptions import (
    AuthorizationException,
    BadRequestException,
    NotFoundException,
)
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.domain.entity.laporan import Laporan, LaporanHilang, LaporanTemuan


class UpdateLaporanDetailsRequest:
    def __init__(
        self,
        laporan_id: UUID,
        user_id: UUID,
        location_id: UUID,
        date: date,
    ) -> None:
        self.laporan_id = laporan_id
        self.user_id = user_id
        self.location_id = location_id
        self.date = date


class UpdateLaporanDetailsResult:
    def __init__(self, laporan: Laporan) -> None:
        self.laporan = laporan


class UpdateLaporanDetailsUsecase:
    """Update the location and date of an existing laporan."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        lokasi_repository: ILokasiRepository,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._lokasi_repository = lokasi_repository

    async def execute(
        self, request: UpdateLaporanDetailsRequest
    ) -> UpdateLaporanDetailsResult:
        """Authorize the caller and update the laporan-type-specific details."""
        laporan = await self._laporan_repository.findById(request.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        if laporan.user_id != request.user_id:
            raise AuthorizationException(
                "Kamu tidak memiliki izin untuk mengakses resource ini",
            )

        lokasi = await self._lokasi_repository.find_by_id(request.location_id)
        if lokasi is None:
            raise NotFoundException("Lokasi tidak ditemukan")

        try:
            if isinstance(laporan, LaporanHilang):
                laporan.update(
                    lost_at_location_id=request.location_id,
                    lost_at_date=request.date,
                )
            elif isinstance(laporan, LaporanTemuan):
                laporan.update(
                    found_at_location_id=request.location_id,
                    found_at_date=request.date,
                )
            else:
                raise BadRequestException(f"Unsupported laporan type: {laporan.type}")
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        updated_laporan = await self._laporan_repository.update(laporan)
        return UpdateLaporanDetailsResult(laporan=updated_laporan)
