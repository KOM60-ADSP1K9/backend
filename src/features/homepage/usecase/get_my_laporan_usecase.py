"""Usecase: Get laporan created by the current user for the homepage."""

from collections.abc import Iterable
from datetime import date
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.tables.barang_table import BarangTable
from src.infrastructure.tables.laporan_table import LaporanTable
from src.domain.entity.laporan import LaporanStatus, LaporanType


class GetMyLaporanResult:
    def __init__(self, laporan: Iterable[LaporanTable]) -> None:
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
        date: date | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> GetMyLaporanResult:
        """Return the current user's laporan, optionally filtered and paginated."""
        offset = (page - 1) * limit
        statement = (
            select(LaporanTable)
            .options(
                selectinload(LaporanTable.barang).selectinload(
                    BarangTable.kategori_barang
                ),
                selectinload(LaporanTable.user),
                selectinload(LaporanTable.lost_at_location),
                selectinload(LaporanTable.found_at_location),
            )
            .where(LaporanTable.user_id == user_id)
            .order_by(LaporanTable.created_at.desc(), LaporanTable.id.desc())
            .offset(offset)
            .limit(limit)
        )

        if laporan_type is not None:
            statement = statement.where(LaporanTable.type == laporan_type)

        if status is not None:
            statement = statement.where(LaporanTable.status == status)

        if date is not None:
            statement = statement.where(
                or_(
                    LaporanTable.lost_at_date == date,
                    LaporanTable.found_at_date == date,
                )
            )

        if date_from is not None:
            statement = statement.where(
                or_(
                    LaporanTable.lost_at_date >= date_from,
                    LaporanTable.found_at_date >= date_from,
                )
            )

        if date_to is not None:
            statement = statement.where(
                or_(
                    LaporanTable.lost_at_date <= date_to,
                    LaporanTable.found_at_date <= date_to,
                )
            )

        result = await self._db.execute(statement)
        laporan = list(result.scalars().all())
        return GetMyLaporanResult(laporan=laporan)
