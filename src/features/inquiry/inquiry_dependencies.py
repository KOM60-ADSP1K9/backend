"""Dependency providers for inquiry features."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.i_storage_service import IStorageService
from src.core.db import get_async_db_session
from src.domain.entity.i_inquiry_repository import IInquiryRepository
from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.features.inquiry.usecase.create_claim_inquiry_usecase import (
    CreateClaimInquiryUsecase,
)
from src.features.inquiry.usecase.create_found_inquiry_usecase import (
    CreateFoundInquiryUsecase,
)
from src.features.inquiry.usecase.update_inquiry_status_usecase import (
    UpdateInquiryStatusUsecase,
)
from src.infrastructure.repositories.inquiry_repository import InquiryRepository
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.services.storage_service_factory import create_storage_service


def get_laporan_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> ILaporanRepository:
    return LaporanRepository(db)


def get_inquiry_repository(
    db: AsyncSession = Depends(get_async_db_session),
) -> IInquiryRepository:
    return InquiryRepository(db)


def get_storage_service() -> IStorageService:
    return create_storage_service()


def get_create_claim_inquiry_usecase(
    laporan_repository: ILaporanRepository = Depends(get_laporan_repository),
    storage_service: IStorageService = Depends(get_storage_service),
) -> CreateClaimInquiryUsecase:
    return CreateClaimInquiryUsecase(
        laporan_repository=laporan_repository,
        storage_service=storage_service,
    )


def get_create_found_inquiry_usecase(
    laporan_repository: ILaporanRepository = Depends(get_laporan_repository),
    storage_service: IStorageService = Depends(get_storage_service),
) -> CreateFoundInquiryUsecase:
    return CreateFoundInquiryUsecase(
        laporan_repository=laporan_repository,
        storage_service=storage_service,
    )


def get_update_inquiry_status_usecase(
    laporan_repository: ILaporanRepository = Depends(get_laporan_repository),
    inquiry_repository: IInquiryRepository = Depends(get_inquiry_repository),
) -> UpdateInquiryStatusUsecase:
    return UpdateInquiryStatusUsecase(
        laporan_repository=laporan_repository,
        inquiry_repository=inquiry_repository,
    )
