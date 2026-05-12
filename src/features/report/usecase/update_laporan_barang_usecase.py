"""Usecase for updating the barang attached to a laporan."""

from uuid import UUID

from src.application.i_storage_service import IStorageService
from src.core.exceptions import (
    AuthorizationException,
    BadRequestException,
    NotFoundException,
)
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.laporan import Laporan


class UpdateLaporanBarangRequest:
    def __init__(
        self,
        laporan_id: UUID,
        user_id: UUID,
        barang_name: str,
        barang_description: str,
        photo_content: bytes | None,
        photo_filename: str | None,
    ) -> None:
        self.laporan_id = laporan_id
        self.user_id = user_id
        self.barang_name = barang_name
        self.barang_description = barang_description
        self.photo_content = photo_content
        self.photo_filename = photo_filename


class UpdateLaporanBarangResult:
    def __init__(self, laporan: Laporan) -> None:
        self.laporan = laporan


class UpdateLaporanBarangUsecase:
    """Update the barang attached to an existing laporan."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        storage_service: IStorageService,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._storage_service = storage_service

    async def execute(
        self, request: UpdateLaporanBarangRequest
    ) -> UpdateLaporanBarangResult:
        """Authorize the caller, upload a new photo if provided, and update barang."""
        laporan = await self._laporan_repository.findById(request.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        if laporan.user_id != request.user_id:
            raise AuthorizationException(
                "Kamu tidak memiliki izin untuk mengakses resource ini",
            )

        if laporan.barang is None:
            raise NotFoundException("Barang tidak ditemukan")

        previous_photo = laporan.barang.photo
        if request.photo_content is not None:
            photo_path = await self._storage_service.upload_photo(
                request.photo_content,
                request.photo_filename or "photo",
            )
        else:
            photo_path = previous_photo

        try:
            laporan.updateBarang(
                name=request.barang_name,
                description=request.barang_description,
                photo=photo_path,
            )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        updated_laporan = await self._laporan_repository.update(laporan)

        if (
            request.photo_content is not None
            and previous_photo
            and previous_photo != photo_path
        ):
            await self._storage_service.delete_photo(previous_photo)

        return UpdateLaporanBarangResult(laporan=updated_laporan)
