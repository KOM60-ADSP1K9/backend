from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.i_laporan_repository import ILaporanRepository
from src.domain.entity.laporan import Laporan
from src.infrastructure.tables.laporan_table import LaporanTable


class LaporanRepository(ILaporanRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save(self, entity: Laporan) -> Laporan:
        row = LaporanTable.from_domain(entity)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row.to_domain()

    async def update(self, entity: Laporan) -> Laporan:
        row = LaporanTable.from_domain(entity)
        merged = await self.db.merge(row)
        await self.db.commit()
        await self.db.refresh(merged)
        return merged.to_domain()

    async def saveAll(self, entities: Iterable[Laporan]) -> Iterable[Laporan]:
        rows = [LaporanTable.from_domain(entity) for entity in entities]
        self.db.add_all(rows)
        await self.db.commit()
        for row in rows:
            await self.db.refresh(row)
        return [row.to_domain() for row in rows]

    async def findById(self, id: UUID) -> Laporan | None:
        result = await self.db.execute(
            select(LaporanTable).where(LaporanTable.id == id)
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_domain()

    async def existsById(self, id: UUID) -> bool:
        result = await self.db.execute(
            select(LaporanTable.id).where(LaporanTable.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def findAll(self) -> Iterable[Laporan]:
        result = await self.db.execute(select(LaporanTable))
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def findAllById(self, ids: Iterable[UUID]) -> Iterable[Laporan]:
        ids_list = list(ids)
        if not ids_list:
            return []

        result = await self.db.execute(
            select(LaporanTable).where(LaporanTable.id.in_(ids_list))
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(LaporanTable))
        return int(result.scalar_one())

    async def deleteById(self, id: UUID) -> None:
        await self.db.execute(delete(LaporanTable).where(LaporanTable.id == id))
        await self.db.commit()

    async def delete(self, entity: Laporan) -> None:
        await self.deleteById(entity.id)

    async def deleteAllById(self, ids: Iterable[UUID]) -> None:
        ids_list = list(ids)
        if not ids_list:
            return

        await self.db.execute(delete(LaporanTable).where(LaporanTable.id.in_(ids_list)))
        await self.db.commit()

    async def deleteAll(self, entities: Iterable[Laporan] | None = None) -> None:
        if entities is None:
            await self.db.execute(delete(LaporanTable))
            await self.db.commit()
            return

        entity_ids = [entity.id for entity in entities]
        await self.deleteAllById(entity_ids)
