from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession


from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.domain.entity.lokasi import Lokasi
from src.infrastructure.tables import LokasiTable


class LokasiRepository(ILokasiRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> Iterable[Lokasi]:
        result = await self.db.execute(
            select(LokasiTable).order_by(asc(LokasiTable.name))
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def find_by_id(self, lokasi_id: UUID) -> Lokasi | None:
        result = await self.db.execute(
            select(LokasiTable).where(LokasiTable.id == lokasi_id)
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_domain()

    async def find_all_by_ids(self, lokasi_ids: Iterable[UUID]) -> Iterable[Lokasi]:
        lokasi_ids_list = list(lokasi_ids)
        if not lokasi_ids_list:
            return []

        result = await self.db.execute(
            select(LokasiTable)
            .where(LokasiTable.id.in_(lokasi_ids_list))
            .order_by(asc(LokasiTable.name))
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]
