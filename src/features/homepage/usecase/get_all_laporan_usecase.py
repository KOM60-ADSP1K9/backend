"""Usecase: Get all laporan for the homepage."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.infrastructure.tables.laporan_table import LaporanTable


class GetAllLaporanResult:
    def __init__(self, laporan: Iterable[Laporan]) -> None:
        self.laporan = laporan


class GetAllLaporanUsecase:
    """Get-all-laporan use case with injected database session."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def execute(
        self,
        laporan_type: LaporanType | None = None,
        status: LaporanStatus | None = None,
    ) -> GetAllLaporanResult:
        """Return laporan in the system, optionally filtered by type and status."""
        statement = select(LaporanTable).options(selectinload(LaporanTable.barang))

        if laporan_type is not None:
            statement = statement.where(LaporanTable.type == laporan_type)

        if status is not None:
            statement = statement.where(LaporanTable.status == status)

        result = await self._db.execute(statement)
        laporan = [row.to_domain() for row in result.scalars().all()]
        return GetAllLaporanResult(laporan=laporan)
