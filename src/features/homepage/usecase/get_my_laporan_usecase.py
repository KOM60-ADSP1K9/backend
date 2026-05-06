"""Usecase: Get laporan created by the current user for the homepage."""

from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity.laporan import Laporan, LaporanStatus, LaporanType
from src.infrastructure.tables.laporan_table import LaporanTable


class GetMyLaporanResult:
    def __init__(self, laporan: Iterable[Laporan]) -> None:
        self.laporan = laporan


class GetMyLaporanUsecase:
    """Get-my-laporan use case with injected database session."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def execute(
        self,
        user_id: UUID,
        laporan_type: LaporanType | None = None,
        status: LaporanStatus | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> GetMyLaporanResult:
        """Return the current user's laporan, optionally filtered and paginated."""
        offset = (page - 1) * limit
        statement = (
            select(LaporanTable)
            .options(selectinload(LaporanTable.barang))
            .where(LaporanTable.user_id == user_id)
            .order_by(LaporanTable.created_at.desc(), LaporanTable.id.desc())
            .offset(offset)
            .limit(limit)
        )

        if laporan_type is not None:
            statement = statement.where(LaporanTable.type == laporan_type)

        if status is not None:
            statement = statement.where(LaporanTable.status == status)

        result = await self._db.execute(statement)
        laporan = [row.to_domain() for row in result.scalars().all()]
        return GetMyLaporanResult(laporan=laporan)
