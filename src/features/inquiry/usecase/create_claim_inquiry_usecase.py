"""Usecase for creating a ClaimInquiry on an active LaporanTemuan."""

from uuid import UUID

from src.application.i_storage_service import IStorageService
from src.core.exceptions import BadRequestException, NotFoundException
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.inquiry import ClaimInquiry, Inquiry
from src.domain.entity.laporan import LaporanTemuan


class CreateClaimInquiryRequest:
    def __init__(
        self,
        laporan_id: UUID,
        sender_user_id: UUID,
        message_content: str,
        claimer_contact: str,
        proof_of_ownership_content: bytes,
        proof_of_ownership_filename: str,
        ktm_content: bytes,
        ktm_filename: str,
    ) -> None:
        self.laporan_id = laporan_id
        self.sender_user_id = sender_user_id
        self.message_content = message_content
        self.claimer_contact = claimer_contact
        self.proof_of_ownership_content = proof_of_ownership_content
        self.proof_of_ownership_filename = proof_of_ownership_filename
        self.ktm_content = ktm_content
        self.ktm_filename = ktm_filename


class CreateClaimInquiryResult:
    def __init__(self, inquiry: Inquiry) -> None:
        self.inquiry = inquiry


class CreateClaimInquiryUsecase:
    """Create a ClaimInquiry against an active LaporanTemuan (aggregate root)."""

    def __init__(
        self,
        laporan_repository: ILaporanRepository,
        storage_service: IStorageService,
    ) -> None:
        self._laporan_repository = laporan_repository
        self._storage_service = storage_service

    async def execute(
        self, request: CreateClaimInquiryRequest
    ) -> CreateClaimInquiryResult:
        laporan = await self._laporan_repository.findById(request.laporan_id)
        if laporan is None:
            raise NotFoundException("Laporan tidak ditemukan")

        if not isinstance(laporan, LaporanTemuan):
            raise BadRequestException("LaporanTemuan can only accept ClaimInquiry")

        proof_path = await self._storage_service.upload_photo(
            request.proof_of_ownership_content,
            request.proof_of_ownership_filename,
        )
        ktm_path = await self._storage_service.upload_photo(
            request.ktm_content,
            request.ktm_filename,
        )

        inquiry = ClaimInquiry.New(
            laporan_id=request.laporan_id,
            sender_user_id=request.sender_user_id,
            message_content=request.message_content,
            claimer_contact=request.claimer_contact,
            proof_of_ownership=proof_path,
            ktm=ktm_path,
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
        return CreateClaimInquiryResult(inquiry=saved_inquiry)
