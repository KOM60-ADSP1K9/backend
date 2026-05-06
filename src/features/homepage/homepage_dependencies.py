"""Dependency providers for homepage use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_db_session
from src.features.homepage.usecase.get_all_laporan_usecase import (
    GetAllLaporanUsecase,
)
from src.features.homepage.usecase.get_my_laporan_usecase import (
    GetMyLaporanUsecase,
)


def get_all_laporan_usecase(
    db: AsyncSession = Depends(get_async_db_session),
) -> GetAllLaporanUsecase:
    return GetAllLaporanUsecase(db=db)


def get_my_laporan_usecase(
    db: AsyncSession = Depends(get_async_db_session),
) -> GetMyLaporanUsecase:
    return GetMyLaporanUsecase(db=db)
