"""Usecase for transitioning an inquiry's status (owner-only)."""

from uuid import UUID

from src.core.exceptions import (
    AuthorizationException,
    BadRequestException,
    NotFoundException,
)
from src.domain.entity.i_inquiry_repository import IInquiryRepository
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.inquiry import Inquiry, InquiryStatus


class UpdateInquiryStatusRequest:
    def __init__(
        self,
        inquiry_id: UUID,
        target_status: InquiryStatus,
        current_user_id: UUID,
    ) -> None:
        self.inquiry_id = inquiry_id
        self.target_status = target_status
        self.current_user_id = current_user_id


class UpdateInquiryStatusResult:
    def __init__(self, inquiry: Inquiry) -> None:
        self.inquiry = inquiry


class UpdateInquiryStatusUsecase:
    """Transition an inquiry's status. Only the laporan owner may invoke."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        inquiry_repository: IInquiryRepository,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._inquiry_repository = inquiry_repository

    async def execute(
        self, request: UpdateInquiryStatusRequest
    ) -> UpdateInquiryStatusResult:
        inquiry_stub = await self._inquiry_repository.findById(request.inquiry_id)
        if inquiry_stub is None:
            raise NotFoundException("Inquiry tidak ditemukan")

        laporan = await self._laporan_repository.findById(inquiry_stub.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        if laporan.user_id != request.current_user_id:
            raise AuthorizationException(
                "Kamu tidak memiliki izin untuk mengakses resource ini"
            )

        target_inquiry = next(
            (i for i in laporan.inquiries if i.id == request.inquiry_id),
            None,
        )
        if target_inquiry is None:
            raise NotFoundException("Inquiry tidak ditemukan")

        try:
            if request.target_status == InquiryStatus.ACTIVE:
                laporan.make_inquiry_active(target_inquiry)
            elif request.target_status == InquiryStatus.REJECTED:
                laporan.reject_inquiry(target_inquiry)
            else:
                raise BadRequestException(
                    f"Invalid target status: {request.target_status}"
                )
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        saved_laporan = await self._laporan_repository.update(laporan)

        saved_inquiry = next(
            (i for i in saved_laporan.inquiries if i.id == request.inquiry_id),
            target_inquiry,
        )
        return UpdateInquiryStatusResult(inquiry=saved_inquiry)
