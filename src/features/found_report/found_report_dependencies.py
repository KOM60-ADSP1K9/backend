"""Dependency providers for found report creation."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.i_storage_service import IStorageService
from src.core.db import get_async_db_session
from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.features.found_report.usecase.create_found_report_usecase import (
    CreateFoundReportUsecase,
)
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.repositories.lokasi_repository import LokasiRepository
from src.infrastructure.services.storage_service_factory import create_storage_service


def get_laporan_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> LaporanRepository:
    return LaporanRepository(db)


def get_lokasi_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> LokasiRepository:
    return LokasiRepository(db)


def get_storage_service() -> IStorageService:
    return create_storage_service()


def get_create_found_report_usecase(
    laporan_repository: LaporanRepository = Depends(get_laporan_repository),
    lokasi_repository: ILokasiRepository = Depends(get_lokasi_repository),
    storage_service: IStorageService = Depends(get_storage_service),
) -> CreateFoundReportUsecase:
    return CreateFoundReportUsecase(
        laporan_repository=laporan_repository,
        lokasi_repository=lokasi_repository,
        storage_service=storage_service,
    )
