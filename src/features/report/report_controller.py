"""Report controller.

GET   /reports/{laporan_id} – Get laporan detail with all inquiries (authenticated)
PATCH /reports/{laporan_id}/status – Update laporan status (owner only)
PATCH /reports/{laporan_id}/barang – Update laporan barang (owner only)
PATCH /reports/{laporan_id}/details – Update laporan location and date (owner only)
DELETE /reports/{laporan_id} – Delete a draft laporan (owner only)
"""

import enum
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict

from src.core.auth import get_current_user
from src.core.exceptions import BadRequestException, RequestTooLargeException
from src.core.http import HTTPDataResponse, HTTPMessageResponse
from src.core.validators import TodayOrPastDate
from src.domain.entity.barang import Barang
from src.domain.entity.inquiry import InquiryStatus, InquiryType
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.domain.entity.user import User
from src.features.report.report_dependencies import (
    get_delete_laporan_usecase,
    get_laporan_detail_usecase,
    get_update_laporan_barang_usecase,
    get_update_laporan_details_usecase,
    get_update_laporan_status_usecase,
)
from src.features.report.usecase.delete_laporan_usecase import (
    DeleteLaporanRequest,
    DeleteLaporanUsecase,
)
from src.features.report.usecase.get_laporan_detail_usecase import (
    GetLaporanDetailUsecase,
)
from src.features.report.usecase.update_laporan_barang_usecase import (
    UpdateLaporanBarangRequest,
    UpdateLaporanBarangUsecase,
)
from src.features.report.usecase.update_laporan_details_usecase import (
    UpdateLaporanDetailsRequest,
    UpdateLaporanDetailsUsecase,
)
from src.features.report.usecase.update_laporan_status_usecase import (
    UpdateLaporanStatusRequest,
    UpdateLaporanStatusUsecase,
)
from src.infrastructure.tables.inquiry_table import InquiryTable
from src.infrastructure.tables.laporan_table import LaporanTable

report_router = APIRouter(prefix="/reports", tags=["reports_management"])


class LaporanDetailKategoriBarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class LaporanDetailBarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    photo: str
    kategori_barang_id: UUID | None = None
    kategori_barang: LaporanDetailKategoriBarangResponseDto | None = None
    created_at: datetime | None
    updated_at: datetime | None


class LaporanDetailUserResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    nim: str | None
    nip: str | None


class LaporanDetailInquiryResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: InquiryType
    status: InquiryStatus
    laporan_id: UUID
    sender_user_id: UUID
    sender: LaporanDetailUserResponseDto | None
    message_content: str
    send_date: datetime
    claimer_contact: str | None = None
    proof_of_ownership: str | None = None
    ktm: str | None = None
    finder_contact: str | None = None
    photo: str | None = None
    created_at: datetime | None
    updated_at: datetime | None
    is_owned: bool


class LaporanDetailResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    found_at_location_id: UUID | None
    found_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    barang: LaporanDetailBarangResponseDto
    user: LaporanDetailUserResponseDto | None
    is_owned: bool
    inquiries: list[LaporanDetailInquiryResponseDto]


def _to_laporan_detail_inquiry_response_dto(
    inquiry: InquiryTable,
    current_user_id: UUID,
) -> LaporanDetailInquiryResponseDto:
    return LaporanDetailInquiryResponseDto(
        id=inquiry.id,
        type=inquiry.type,
        status=inquiry.status,
        laporan_id=inquiry.laporan_id,
        sender_user_id=inquiry.sender_user_id,
        sender=(
            LaporanDetailUserResponseDto.model_validate(inquiry.sender)
            if inquiry.sender is not None
            else None
        ),
        message_content=inquiry.message_content,
        send_date=inquiry.send_date,
        claimer_contact=inquiry.claimer_contact,
        proof_of_ownership=inquiry.proof_of_ownership,
        ktm=inquiry.ktm,
        finder_contact=inquiry.finder_contact,
        photo=inquiry.photo,
        created_at=inquiry.created_at,
        updated_at=inquiry.updated_at,
        is_owned=inquiry.sender_user_id == current_user_id,
    )


def _to_laporan_detail_response_dto(
    laporan: LaporanTable,
    current_user_id: UUID,
) -> LaporanDetailResponseDto:
    return LaporanDetailResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
        lost_at_date=getattr(laporan, "lost_at_date", None),
        found_at_location_id=getattr(laporan, "found_at_location_id", None),
        found_at_date=getattr(laporan, "found_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        barang=LaporanDetailBarangResponseDto.model_validate(laporan.barang),
        user=(
            LaporanDetailUserResponseDto.model_validate(laporan.user)
            if laporan.user is not None
            else None
        ),
        is_owned=laporan.user_id == current_user_id,
        inquiries=[
            _to_laporan_detail_inquiry_response_dto(inquiry, current_user_id)
            for inquiry in laporan.inquiries
        ],
    )


@report_router.get(
    "/{laporan_id}",
    response_model=HTTPDataResponse[LaporanDetailResponseDto],
)
async def get_laporan_detail(
    laporan_id: UUID,
    current_user: User = Depends(get_current_user),
    usecase: GetLaporanDetailUsecase = Depends(get_laporan_detail_usecase),
) -> HTTPDataResponse[LaporanDetailResponseDto]:
    """Get a single laporan with all its inquiries."""
    result = await usecase.execute(laporan_id=laporan_id)

    return HTTPDataResponse[LaporanDetailResponseDto](
        status="success",
        data=_to_laporan_detail_response_dto(result.laporan, current_user.id),
        message="Laporan detail fetched successfully",
    )


class UserUpdatableLaporanStatus(str, enum.Enum):
    """Laporan statuses a user is allowed to set. CLAIM_PENDING is system-driven."""

    ACTIVE = LaporanStatus.ACTIVE.value
    RESOLVED = LaporanStatus.RESOLVED.value
    SELF_RESOLVED = LaporanStatus.SELF_RESOLVED.value
    CLOSED = LaporanStatus.CLOSED.value


class UpdateLaporanStatusRequestDto(BaseModel):
    status: UserUpdatableLaporanStatus


class BarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    photo: str
    kategori_barang_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class UpdateLaporanStatusResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    found_at_location_id: UUID | None
    found_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    barang: BarangResponseDto | None


def _to_update_laporan_status_response_dto(
    laporan: Laporan,
) -> UpdateLaporanStatusResponseDto:
    return UpdateLaporanStatusResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
        lost_at_date=getattr(laporan, "lost_at_date", None),
        found_at_location_id=getattr(laporan, "found_at_location_id", None),
        found_at_date=getattr(laporan, "found_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        barang=(
            BarangResponseDto.model_validate(laporan.barang)
            if laporan.barang is not None
            else None
        ),
    )


@report_router.patch(
    "/{laporan_id}/status",
    response_model=HTTPDataResponse[UpdateLaporanStatusResponseDto],
)
async def update_laporan_status(
    laporan_id: UUID,
    body: UpdateLaporanStatusRequestDto,
    current_user: User = Depends(get_current_user),
    usecase: UpdateLaporanStatusUsecase = Depends(get_update_laporan_status_usecase),
) -> HTTPDataResponse[UpdateLaporanStatusResponseDto]:
    """Update the status of an existing laporan. Owner only."""
    result = await usecase.execute(
        UpdateLaporanStatusRequest(
            laporan_id=laporan_id,
            new_status=LaporanStatus(body.status.value),
            user_id=current_user.id,
            user_role=current_user.role,
        )
    )

    return HTTPDataResponse[UpdateLaporanStatusResponseDto](
        status="success",
        data=_to_update_laporan_status_response_dto(result.laporan),
        message="Laporan status updated successfully",
    )


class UpdateLaporanBarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    found_at_location_id: UUID | None
    found_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    barang: BarangResponseDto


def _to_update_laporan_barang_response_dto(
    laporan: Laporan,
) -> UpdateLaporanBarangResponseDto:
    return UpdateLaporanBarangResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
        lost_at_date=getattr(laporan, "lost_at_date", None),
        found_at_location_id=getattr(laporan, "found_at_location_id", None),
        found_at_date=getattr(laporan, "found_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        barang=BarangResponseDto.model_validate(laporan.barang),
    )


@report_router.patch(
    "/{laporan_id}/barang",
    response_model=HTTPDataResponse[UpdateLaporanBarangResponseDto],
)
async def update_laporan_barang(
    laporan_id: UUID,
    barang_name: str = Form(...),
    barang_description: str = Form(...),
    kategori_barang_id: UUID = Form(...),
    photo: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    usecase: UpdateLaporanBarangUsecase = Depends(get_update_laporan_barang_usecase),
) -> HTTPDataResponse[UpdateLaporanBarangResponseDto]:
    """Update the barang of an existing laporan. Owner only. Photo is optional."""
    photo_content: bytes | None = None
    photo_filename: str | None = None
    if photo is not None:
        if photo.content_type not in Barang.ALLOWED_PHOTO_TYPES:
            raise BadRequestException(
                f"Invalid photo type. Allowed types: {', '.join(Barang.ALLOWED_PHOTO_TYPES)}"
            )

        if photo.size > Barang.MAX_PHOTO_SIZE_MB * 1024 * 1024:
            raise RequestTooLargeException(
                f"Photo exceeds maximum size of {Barang.MAX_PHOTO_SIZE_MB} MB"
            )

        photo_content = await photo.read()
        photo_filename = photo.filename or "photo"

    result = await usecase.execute(
        UpdateLaporanBarangRequest(
            laporan_id=laporan_id,
            user_id=current_user.id,
            barang_name=barang_name,
            barang_description=barang_description,
            kategori_barang_id=kategori_barang_id,
            photo_content=photo_content,
            photo_filename=photo_filename,
        )
    )

    return HTTPDataResponse[UpdateLaporanBarangResponseDto](
        status="success",
        data=_to_update_laporan_barang_response_dto(result.laporan),
        message="Laporan barang updated successfully",
    )


class UpdateLaporanDetailsRequestDto(BaseModel):
    location_id: UUID
    date: TodayOrPastDate


class UpdateLaporanDetailsResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    found_at_location_id: UUID | None
    found_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    barang: BarangResponseDto | None


def _to_update_laporan_details_response_dto(
    laporan: Laporan,
) -> UpdateLaporanDetailsResponseDto:
    return UpdateLaporanDetailsResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
        lost_at_date=getattr(laporan, "lost_at_date", None),
        found_at_location_id=getattr(laporan, "found_at_location_id", None),
        found_at_date=getattr(laporan, "found_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        barang=(
            BarangResponseDto.model_validate(laporan.barang)
            if laporan.barang is not None
            else None
        ),
    )


@report_router.patch(
    "/{laporan_id}/details",
    response_model=HTTPDataResponse[UpdateLaporanDetailsResponseDto],
)
async def update_laporan_details(
    laporan_id: UUID,
    body: UpdateLaporanDetailsRequestDto,
    current_user: User = Depends(get_current_user),
    usecase: UpdateLaporanDetailsUsecase = Depends(get_update_laporan_details_usecase),
) -> HTTPDataResponse[UpdateLaporanDetailsResponseDto]:
    """Update the location and date of a laporan. Maps to lost_at_* or found_at_* based on type."""
    result = await usecase.execute(
        UpdateLaporanDetailsRequest(
            laporan_id=laporan_id,
            user_id=current_user.id,
            location_id=body.location_id,
            date=body.date,
        )
    )

    return HTTPDataResponse[UpdateLaporanDetailsResponseDto](
        status="success",
        data=_to_update_laporan_details_response_dto(result.laporan),
        message="Laporan details updated successfully",
    )


@report_router.delete(
    "/{laporan_id}",
    response_model=HTTPMessageResponse,
)
async def delete_laporan(
    laporan_id: UUID,
    current_user: User = Depends(get_current_user),
    usecase: DeleteLaporanUsecase = Depends(get_delete_laporan_usecase),
) -> HTTPMessageResponse:
    """Delete a laporan. Owner only. Allowed only when status is draft or active."""
    await usecase.execute(
        DeleteLaporanRequest(
            laporan_id=laporan_id,
            user_id=current_user.id,
        )
    )

    return HTTPMessageResponse(
        status="success",
        message="Laporan deleted successfully",
    )
