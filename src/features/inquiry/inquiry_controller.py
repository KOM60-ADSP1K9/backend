"""Inquiry controller.

POST /inquiries/claim – Create a ClaimInquiry on an active LaporanTemuan.
POST /inquiries/found – Create a FoundInquiry on an active LaporanHilang.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict

from src.core.auth import get_current_user
from src.core.exceptions import BadRequestException, RequestTooLargeException
from src.core.http import HTTPDataResponse
from src.domain.entity.barang import Barang
from src.domain.entity.inquiry import (
    ClaimInquiry,
    FoundInquiry,
    Inquiry,
    InquiryStatus,
    InquiryType,
)
from src.domain.entity.user import User
from src.features.inquiry.inquiry_dependencies import (
    get_create_claim_inquiry_usecase,
    get_create_found_inquiry_usecase,
)
from src.features.inquiry.usecase.create_claim_inquiry_usecase import (
    CreateClaimInquiryRequest,
    CreateClaimInquiryUsecase,
)
from src.features.inquiry.usecase.create_found_inquiry_usecase import (
    CreateFoundInquiryRequest,
    CreateFoundInquiryUsecase,
)

inquiry_router = APIRouter(prefix="/inquiries", tags=["inquiries"])


class InquiryResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: InquiryType
    status: InquiryStatus
    laporan_id: UUID
    sender_user_id: UUID
    message_content: str
    send_date: datetime
    claimer_contact: str | None = None
    proof_of_ownership: str | None = None
    ktm: str | None = None
    finder_contact: str | None = None
    photo: str | None = None
    created_at: datetime | None
    updated_at: datetime | None


def _to_inquiry_response_dto(inquiry: Inquiry) -> InquiryResponseDto:
    return InquiryResponseDto(
        id=inquiry.id,
        type=inquiry.type,
        status=inquiry.status,
        laporan_id=inquiry.laporan_id,
        sender_user_id=inquiry.sender_user_id,
        message_content=inquiry.message_content,
        send_date=inquiry.send_date,
        claimer_contact=(
            getattr(inquiry, "claimer_contact", None)
            if isinstance(inquiry, ClaimInquiry)
            else None
        ),
        proof_of_ownership=(
            getattr(inquiry, "proof_of_ownership", None)
            if isinstance(inquiry, ClaimInquiry)
            else None
        ),
        ktm=(
            getattr(inquiry, "ktm", None) if isinstance(inquiry, ClaimInquiry) else None
        ),
        finder_contact=(
            getattr(inquiry, "finder_contact", None)
            if isinstance(inquiry, FoundInquiry)
            else None
        ),
        photo=(
            getattr(inquiry, "photo", None)
            if isinstance(inquiry, FoundInquiry)
            else None
        ),
        created_at=inquiry.created_at,
        updated_at=inquiry.updated_at,
    )


def _validate_photo(upload: UploadFile, field_label: str) -> None:
    if upload.content_type not in Barang.ALLOWED_PHOTO_TYPES:
        raise BadRequestException(
            f"Invalid {field_label} type. Allowed types: "
            f"{', '.join(Barang.ALLOWED_PHOTO_TYPES)}"
        )

    if upload.size is not None and upload.size > Barang.MAX_PHOTO_SIZE_MB * 1024 * 1024:
        raise RequestTooLargeException(
            f"{field_label} exceeds maximum size of {Barang.MAX_PHOTO_SIZE_MB} MB"
        )


@inquiry_router.post(
    "/claim",
    response_model=HTTPDataResponse[InquiryResponseDto],
    status_code=201,
)
async def create_claim_inquiry(
    laporan_id: UUID = Form(...),
    message_content: str = Form(...),
    claimer_contact: str = Form(...),
    proof_of_ownership: UploadFile = File(...),
    ktm: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    usecase: CreateClaimInquiryUsecase = Depends(get_create_claim_inquiry_usecase),
) -> HTTPDataResponse[InquiryResponseDto]:
    """Create a claim inquiry for an active LaporanTemuan."""
    _validate_photo(proof_of_ownership, "proof_of_ownership")
    _validate_photo(ktm, "ktm")

    result = await usecase.execute(
        CreateClaimInquiryRequest(
            laporan_id=laporan_id,
            sender_user_id=current_user.id,  # attach current user as sender
            message_content=message_content,
            claimer_contact=claimer_contact,
            proof_of_ownership_content=await proof_of_ownership.read(),
            proof_of_ownership_filename=proof_of_ownership.filename or "proof",
            ktm_content=await ktm.read(),
            ktm_filename=ktm.filename or "ktm",
        )
    )

    return HTTPDataResponse[InquiryResponseDto](
        status="success",
        data=_to_inquiry_response_dto(result.inquiry),
        message="Claim inquiry created successfully",
    )


@inquiry_router.post(
    "/found",
    response_model=HTTPDataResponse[InquiryResponseDto],
    status_code=201,
)
async def create_found_inquiry(
    laporan_id: UUID = Form(...),
    message_content: str = Form(...),
    finder_contact: str = Form(...),
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    usecase: CreateFoundInquiryUsecase = Depends(get_create_found_inquiry_usecase),
) -> HTTPDataResponse[InquiryResponseDto]:
    """Create a found inquiry for an active LaporanHilang."""
    _validate_photo(photo, "photo")

    result = await usecase.execute(
        CreateFoundInquiryRequest(
            laporan_id=laporan_id,
            sender_user_id=current_user.id,  # attach current user as sender
            message_content=message_content,
            finder_contact=finder_contact,
            photo_content=await photo.read(),
            photo_filename=photo.filename or "photo",
        )
    )

    return HTTPDataResponse[InquiryResponseDto](
        status="success",
        data=_to_inquiry_response_dto(result.inquiry),
        message="Found inquiry created successfully",
    )
