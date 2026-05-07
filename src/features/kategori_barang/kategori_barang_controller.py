"""Kategori barang controller – authenticated endpoints.

GET /kategori-barang – Get all kategori barang (authenticated)
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.auth import get_current_user
from src.core.db import get_async_db_session
from src.core.http import HTTPDataResponse
from src.domain.entity.user import User
from src.features.kategori_barang.usecase.get_all_kategori_barang_usecase import (
    GetAllKategoriBarangUsecase,
)
from src.infrastructure.repositories.kategori_barang_repository import (
    KategoriBarangRepository,
)

kategori_barang_router = APIRouter(prefix="/kategori-barang", tags=["kategori_barang"])


class KategoriBarangResponseDto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


@kategori_barang_router.get(
    "",
    response_model=HTTPDataResponse[list[KategoriBarangResponseDto]],
)
async def get_all_kategori_barang(
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db_session),
) -> HTTPDataResponse[list[KategoriBarangResponseDto]]:
    """Get all kategori barang. Requires authentication."""
    usecase = GetAllKategoriBarangUsecase(
        kategori_barang_repository=KategoriBarangRepository(db)
    )
    result = await usecase.execute()

    return HTTPDataResponse[list[KategoriBarangResponseDto]](
        status="success",
        data=[
            KategoriBarangResponseDto.model_validate(item)
            for item in result.kategori_barang
        ],
        message="Kategori barang fetched successfully",
    )
