"""Found report controller.

POST /found-reports – Create found report (Mahasiswa & Staff)
"""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, ConfigDict

from src.core.auth import get_current_user
from src.core.exceptions import BadRequestException, RequestTooLargeException
from src.core.http import HTTPDataResponse
from src.domain.entity.barang import Barang
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.domain.entity.user import User, UserRole
from src.features.found_report.found_report_dependencies import (
    get_create_found_report_usecase,
)
from src.features.found_report.usecase.create_found_report_usecase import (
    CreateFoundReportRequest,
    CreateFoundReportUsecase,
)

found_report_router = APIRouter(prefix="/found-reports", tags=["found_reports"])


class BarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    photo: str
    kategori_barang_id: UUID | None
    created_at: datetime | None
    updated_at: datetime | None


class CreateFoundReportResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    found_at_location_id: UUID | None
    found_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    barang: BarangResponseDto


def _to_create_found_report_response_dto(
    laporan: Laporan,
) -> CreateFoundReportResponseDto:
    return CreateFoundReportResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        found_at_location_id=getattr(laporan, "found_at_location_id", None),
        found_at_date=getattr(laporan, "found_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        barang=BarangResponseDto.model_validate(laporan.barang),
    )


@found_report_router.post(
    "",
    response_model=HTTPDataResponse[CreateFoundReportResponseDto],
    status_code=201,
)
async def create_found_report(
    photo: UploadFile = File(...),
    barang_name: str = Form(...),
    barang_description: str = Form(...),
    kategori_barang_id: UUID = Form(...),
    found_at_location_id: UUID | None = Form(None),
    found_at_date: date = Form(...),
    current_user: User = Depends(get_current_user),
    usecase: CreateFoundReportUsecase = Depends(get_create_found_report_usecase),
) -> HTTPDataResponse[CreateFoundReportResponseDto]:
    """Create a new found report. Staff use their supervised lokasi automatically."""
    if photo.content_type not in Barang.ALLOWED_PHOTO_TYPES:
        raise BadRequestException(
            f"Invalid photo type. Allowed types: {', '.join(Barang.ALLOWED_PHOTO_TYPES)}"
        )

    if photo.size > Barang.MAX_PHOTO_SIZE_MB * 1024 * 1024:  # convert MB to bytes
        raise RequestTooLargeException(
            f"Photo exceeds maximum size of {Barang.MAX_PHOTO_SIZE_MB} MB"
        )

    resolved_found_at_location_id = found_at_location_id
    if current_user.role == UserRole.STAFF:
        if current_user.lokasi_id is None:
            raise BadRequestException("Staff location is not configured")
        resolved_found_at_location_id = current_user.lokasi_id
    elif resolved_found_at_location_id is None:
        raise BadRequestException("found_at_location_id is required for mahasiswa")

    result = await usecase.execute(
        CreateFoundReportRequest(
            photo_content=await photo.read(),
            photo_filename=photo.filename or "photo",
            barang_name=barang_name,
            barang_description=barang_description,
            kategori_barang_id=kategori_barang_id,
            found_at_location_id=resolved_found_at_location_id,
            found_at_date=found_at_date,
            user_id=current_user.id,
        )
    )

    return HTTPDataResponse[CreateFoundReportResponseDto](
        status="success",
        data=_to_create_found_report_response_dto(result.laporan),
        message="Found report created successfully",
    )
