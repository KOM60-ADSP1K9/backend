"""Lokasi controller – location endpoints (authenticated users only).

GET /locations – Get all locations (authenticated)
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.db import get_async_db_session
from src.core.http import HTTPDataResponse
from src.domain.entity.user import User
from src.features.lokasi.usecase.get_all_lokasi_usecase import GetAllLokasiUsecase
from src.infrastructure.repositories.lokasi_repository import LokasiRepository

lokasi_router = APIRouter(prefix="/locations", tags=["locations"])


class LokasiResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    latitude: float
    longitude: float


@lokasi_router.get("", response_model=HTTPDataResponse[list[LokasiResponseDto]])
async def get_all_locations(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[list[LokasiResponseDto]]:
    """Get all locations. Requires authentication."""
    usecase = GetAllLokasiUsecase(lokasi_repository=LokasiRepository(db))
    result = await usecase.execute()

    return HTTPDataResponse[list[LokasiResponseDto]](
        status="success",
        data=[LokasiResponseDto.model_validate(item) for item in result.lokasi],
        message="Locations fetched successfully",
    )
