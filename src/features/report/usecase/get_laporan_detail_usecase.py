"""Usecase: Get a single laporan with all its inquiries."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundException
from src.infrastructure.tables.barang_table import BarangTable
from src.infrastructure.tables.inquiry_table import InquiryTable
from src.infrastructure.tables.laporan_table import LaporanTable


class GetLaporanDetailResult:
    def __init__(self, laporan: LaporanTable) -> None:
        self.laporan = laporan


class GetLaporanDetailUsecase:
    """Get-laporan-detail use case with injected database session."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def execute(self, laporan_id: UUID) -> GetLaporanDetailResult:
        """Return a single laporan with all its inquiries eagerly loaded."""
        statement = (
            select(LaporanTable)
            .options(
                selectinload(LaporanTable.barang).selectinload(
                    BarangTable.kategori_barang
                ),
                selectinload(LaporanTable.user),
                selectinload(LaporanTable.inquiries).selectinload(InquiryTable.sender),
            )
            .where(LaporanTable.id == laporan_id)
        )

        result = await self._db.execute(statement)
        laporan = result.scalars().first()
        if laporan is None:
            raise NotFoundException("Laporan not found")

        return GetLaporanDetailResult(laporan=laporan)
