"""Lost report controller.

POST /lost-reports – Create lost report (Mahasiswa only)
"""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict

from src.core.auth import require_role
from src.core.http import HTTPDataResponse
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.domain.entity.user import User, UserRole
from src.features.lost_report.lost_report_dependencies import (
    get_create_lost_report_usecase,
)
from src.features.lost_report.usecase.create_lost_report_usecase import (
    CreateLostReportRequest,
    CreateLostReportUsecase,
)

lost_report_router = APIRouter(prefix="/lost-reports", tags=["lost_reports"])


class CreateLostReportResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    photo: str
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None


@lost_report_router.post(
    "",
    response_model=HTTPDataResponse[CreateLostReportResponseDto],
    status_code=201,
)
async def create_lost_report(
    photo: UploadFile = File(...),
    lost_at_location_id: UUID = Form(...),
    lost_at_date: date = Form(...),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
    usecase: CreateLostReportUsecase = Depends(get_create_lost_report_usecase),
) -> HTTPDataResponse[CreateLostReportResponseDto]:
    """Create a new lost report. Only mahasiswa can access this endpoint."""
    if photo.content_type not in Laporan.ALLOWED_PHOTO_TYPES:
        return HTTPDataResponse[CreateLostReportResponseDto](
            status="error",
            message="Invalid photo format. Only JPEG and PNG are allowed.",
        )

    if photo.size > Laporan.MAX_PHOTO_SIZE_MB * 1024 * 1024:  # convert MB to bytes
        return HTTPDataResponse[CreateLostReportResponseDto](
            status="error",
            message=f"Photo size exceeds the {Laporan.MAX_PHOTO_SIZE_MB} MB limit.",
        )

    result = await usecase.execute(
        CreateLostReportRequest(
            photo_content=await photo.read(),
            photo_filename=photo.filename or "photo",
            lost_at_location_id=lost_at_location_id,
            lost_at_date=lost_at_date,
            user_id=current_user.id,
        )
    )

    return HTTPDataResponse[CreateLostReportResponseDto](
        status="success",
        data=CreateLostReportResponseDto.model_validate(result.laporan),
        message="Lost report created successfully",
    )
