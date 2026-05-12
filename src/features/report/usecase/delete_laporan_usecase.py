"""Usecase for deleting a laporan."""

from uuid import UUID

from src.application.i_storage_service import IStorageService
from src.core.exceptions import (
    AuthorizationException,
    BadRequestException,
    NotFoundException,
)
from src.domain.entity.i_laporan_repository import ILaporanRepository


class DeleteLaporanRequest:
    def __init__(self, laporan_id: UUID, user_id: UUID) -> None:
        self.laporan_id = laporan_id
        self.user_id = user_id


class DeleteLaporanUsecase:
    """Delete a laporan and its attached barang photo."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        storage_service: IStorageService,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._storage_service = storage_service

    async def execute(self, request: DeleteLaporanRequest) -> None:
        """Authorize the caller, enforce delete invariants, and remove the laporan."""
        laporan = await self._laporan_repository.findById(request.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        if laporan.user_id != request.user_id:
            raise AuthorizationException(
                "Kamu tidak memiliki izin untuk mengakses resource ini",
            )

        try:
            laporan.assert_can_delete()
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        photo_url = laporan.barang.photo if laporan.barang is not None else None

        await self._laporan_repository.deleteById(laporan.id)

        if photo_url:
            await self._storage_service.delete_photo(photo_url)
