"""Lost report controller.

POST /lost-reports – Create lost report (Mahasiswa only)
"""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict

from src.core.exceptions import BadRequestException, RequestTooLargeException
from src.core.auth import require_role
from src.core.http import HTTPDataResponse
from src.domain.entity.barang import Barang
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


class BarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    photo: str
    kategori_barang_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class CreateLostReportResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    barang: BarangResponseDto


def _to_create_lost_report_response_dto(
    laporan: Laporan,
) -> CreateLostReportResponseDto:
    return CreateLostReportResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
        lost_at_date=getattr(laporan, "lost_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        barang=BarangResponseDto.model_validate(laporan.barang),
    )


@lost_report_router.post(
    "",
    response_model=HTTPDataResponse[CreateLostReportResponseDto],
    status_code=201,
)
async def create_lost_report(
    photo: UploadFile = File(...),
    barang_name: str = Form(...),
    barang_description: str = Form(...),
    kategori_barang_id: UUID = Form(...),
    lost_at_location_id: UUID = Form(...),
    lost_at_date: date = Form(...),
    current_user: User = Depends(require_role(UserRole.MAHASISWA)),
    usecase: CreateLostReportUsecase = Depends(get_create_lost_report_usecase),
) -> HTTPDataResponse[CreateLostReportResponseDto]:
    """Create a new lost report. Only mahasiswa can access this endpoint."""
    if photo.content_type not in Barang.ALLOWED_PHOTO_TYPES:
        raise BadRequestException(
            f"Invalid photo type. Allowed types: {', '.join(Barang.ALLOWED_PHOTO_TYPES)}"
        )

    if photo.size > Barang.MAX_PHOTO_SIZE_MB * 1024 * 1024:  # convert MB to bytes
        raise RequestTooLargeException(
            f"Photo exceeds maximum size of {Barang.MAX_PHOTO_SIZE_MB} MB"
        )

    result = await usecase.execute(
        CreateLostReportRequest(
            photo_content=await photo.read(),
            photo_filename=photo.filename or "photo",
            barang_name=barang_name,
            barang_description=barang_description,
            kategori_barang_id=kategori_barang_id,
            lost_at_location_id=lost_at_location_id,
            lost_at_date=lost_at_date,
            user_id=current_user.id,
        )
    )

    return HTTPDataResponse[CreateLostReportResponseDto](
        status="success",
        data=_to_create_lost_report_response_dto(result.laporan),
        message="Lost report created successfully",
    )
