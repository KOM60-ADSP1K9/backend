"""Usecase for updating laporan status."""

from uuid import UUID

from src.core.exceptions import (
    AuthorizationException,
    BadRequestException,
    NotFoundException,
)
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.laporan import Laporan, LaporanStatus
from src.domain.entity.user import UserRole


class UpdateLaporanStatusRequest:
    def __init__(
        self,
        laporan_id: UUID,
        new_status: LaporanStatus,
        user_id: UUID,
        user_role: UserRole,
    ) -> None:
        self.laporan_id = laporan_id
        self.new_status = new_status
        self.user_id = user_id
        self.user_role = user_role


class UpdateLaporanStatusResult:
    def __init__(self, laporan: Laporan) -> None:
        self.laporan = laporan


class UpdateLaporanStatusUsecase:
    """Update the status of an existing laporan."""

    def __init__(self, laporan_repository: ILaporanRepository) -> None:
        self._laporan_repository = laporan_repository

    async def execute(
        self, request: UpdateLaporanStatusRequest
    ) -> UpdateLaporanStatusResult:
        """Authorize the caller and apply the status transition."""
        laporan = await self._laporan_repository.findById(request.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        is_owner = laporan.user_id == request.user_id
        if not is_owner:
            raise AuthorizationException(
                "Kamu tidak memiliki izin untuk mengakses resource ini",
            )

        try:
            laporan.resolve_status_update(request.new_status)
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        updated_laporan = await self._laporan_repository.update(laporan)
        return UpdateLaporanStatusResult(laporan=updated_laporan)
