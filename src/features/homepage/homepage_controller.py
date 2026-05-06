"""Homepage controller – all laporan visible to authenticated users."""

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.db import get_async_db_session
from src.core.http import HTTPDataResponse
from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.domain.entity.user import User
from src.features.homepage.usecase.get_all_laporan_usecase import (
    GetAllLaporanUsecase,
)
from src.infrastructure.repositories.laporan_repository import LaporanRepository

homepage_router = APIRouter(prefix="/homepage", tags=["homepage"])


class HomepageLaporanResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: LaporanType
    status: LaporanStatus
    photo: str
    lost_at_location_id: UUID | None
    lost_at_date: date | None
    found_at_location_id: UUID | None
    found_at_date: date | None
    created_at: datetime | None
    updated_at: datetime | None
    is_owned: bool


def _to_homepage_laporan_response_dto(
    laporan: Laporan,
    current_user_id: UUID,
) -> HomepageLaporanResponseDto:
    return HomepageLaporanResponseDto(
        id=laporan.id,
        type=laporan.type,
        status=laporan.status,
        photo=laporan.photo,
        lost_at_location_id=getattr(laporan, "lost_at_location_id", None),
        lost_at_date=getattr(laporan, "lost_at_date", None),
        found_at_location_id=getattr(laporan, "found_at_location_id", None),
        found_at_date=getattr(laporan, "found_at_date", None),
        created_at=laporan.created_at,
        updated_at=laporan.updated_at,
        is_owned=laporan.user_id == current_user_id,
    )


@homepage_router.get(
    "/laporan",
    response_model=HTTPDataResponse[list[HomepageLaporanResponseDto]],
)
async def get_all_laporan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[list[HomepageLaporanResponseDto]]:
    """Get all laporan visible on the homepage for any authenticated user."""
    usecase = GetAllLaporanUsecase(laporan_repository=LaporanRepository(db))
    result = await usecase.execute()

    return HTTPDataResponse[list[HomepageLaporanResponseDto]](
        status="success",
        data=[
            _to_homepage_laporan_response_dto(laporan, current_user.id)
            for laporan in result.laporan
        ],
        message="Laporan fetched successfully",
    )
