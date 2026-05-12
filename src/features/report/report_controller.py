"""Report controller.

PATCH /reports/{laporan_id}/status – Update laporan status (owner only)
PATCH /reports/{laporan_id}/barang – Update laporan barang (owner only)
PATCH /reports/{laporan_id}/details – Update laporan location and date (owner only)
"""

import enum
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict

from src.core.auth import get_current_user
from src.core.exceptions import BadRequestException, RequestTooLargeException
from src.core.http import HTTPDataResponse
from src.domain.entity.barang import Barang
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.domain.entity.user import User
from src.features.report.report_dependencies import (
    get_update_laporan_barang_usecase,
    get_update_laporan_details_usecase,
    get_update_laporan_status_usecase,
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

report_router = APIRouter(prefix="/reports", tags=["reports_management"])


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
    date: date


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
