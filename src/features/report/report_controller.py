"""Report controller.

PATCH /reports/{laporan_id}/status – Update laporan status (owner only)
"""

import enum
from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from src.core.auth import get_current_user
from src.core.http import HTTPDataResponse
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.domain.entity.user import User
from src.features.report.report_dependencies import (
    get_update_laporan_status_usecase,
)
from src.features.report.usecase.update_laporan_status_usecase import (
    UpdateLaporanStatusRequest,
    UpdateLaporanStatusUsecase,
)

report_router = APIRouter(prefix="/reports", tags=["reports"])


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
