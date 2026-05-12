"""Dependency providers for report use cases."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_async_db_session
from src.features.report.usecase.update_laporan_status_usecase import (
    UpdateLaporanStatusUsecase,
)
from src.infrastructure.repositories.laporan_repository import LaporanRepository


def get_laporan_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> LaporanRepository:
    return LaporanRepository(db)


def get_update_laporan_status_usecase(
    laporan_repository: LaporanRepository = Depends(get_laporan_repository),
) -> UpdateLaporanStatusUsecase:
    return UpdateLaporanStatusUsecase(laporan_repository=laporan_repository)
