"""Usecase for creating a FoundInquiry on an active LaporanHilang."""

from uuid import UUID

from src.application.i_storage_service import IStorageService
from src.core.exceptions import BadRequestException, NotFoundException
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.inquiry import FoundInquiry, Inquiry
from src.domain.entity.laporan import LaporanHilang


class CreateFoundInquiryRequest:
    def __init__(
        self,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        finder_contact: str,
        photo_content: bytes,
        photo_filename: str,
    ) -> None:
        self.laporan_id = laporan_id
        self.sender_user_id = sender_user_id
        self.message_content = message_content
        self.finder_contact = finder_contact
        self.photo_content = photo_content
        self.photo_filename = photo_filename


class CreateFoundInquiryResult:
    def __init__(self, inquiry: Inquiry) -> None:
        self.inquiry = inquiry


class CreateFoundInquiryUsecase:
    """Create a FoundInquiry against an active LaporanHilang (aggregate root)."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        storage_service: IStorageService,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._storage_service = storage_service

    async def execute(
        self, request: CreateFoundInquiryRequest
    ) -> CreateFoundInquiryResult:
        laporan = await self._laporan_repository.findById(request.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        if not isinstance(laporan, LaporanHilang):
            raise BadRequestException("LaporanHilang can only accept FoundInquiry")

        photo_path = await self._storage_service.upload_photo(
            request.photo_content,
            request.photo_filename,
        )

        inquiry = FoundInquiry.New(
            laporan_id=request.laporan_id,
            sender_user_id=request.sender_user_id,
            message_content=request.message_content,
            finder_contact=request.finder_contact,
            photo=photo_path,
        )

        try:
            laporan.add_inquiry(inquiry)
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        saved_laporan = await self._laporan_repository.update(laporan)

        saved_inquiry = next(
            (i for i in saved_laporan.inquiries if i.id == inquiry.id),
            None,
        )
        if saved_inquiry is None:
            saved_inquiry = inquiry
        return CreateFoundInquiryResult(inquiry=saved_inquiry)
