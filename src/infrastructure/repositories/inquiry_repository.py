from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.i_inquiry_repository import IInquiryRepository
from src.domain.entity.inquiry import Inquiry
from src.infrastructure.tables.inquiry_table import InquiryTable


class InquiryRepository(IInquiryRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def save(self, entity: Inquiry) -> Inquiry:
        row = InquiryTable.from_domain(entity)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row.to_domain()

    async def update(self, entity: Inquiry) -> Inquiry:
        row = InquiryTable.from_domain(entity)
        merged = await self.db.merge(row)
        await self.db.commit()
        await self.db.refresh(merged)
        return merged.to_domain()

    async def saveAll(self, entities: Iterable[Inquiry]) -> Iterable[Inquiry]:
        rows = [InquiryTable.from_domain(entity) for entity in entities]
        self.db.add_all(rows)
        await self.db.commit()
        for row in rows:
            await self.db.refresh(row)
        return [row.to_domain() for row in rows]

    async def findById(self, id: UUID) -> Inquiry | None:
        result = await self.db.execute(
            select(InquiryTable).where(InquiryTable.id == id)
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_domain()

    async def existsById(self, id: UUID) -> bool:
        result = await self.db.execute(
            select(InquiryTable.id).where(InquiryTable.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def findAll(self) -> Iterable[Inquiry]:
        result = await self.db.execute(select(InquiryTable))
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def findAllById(self, ids: Iterable[UUID]) -> Iterable[Inquiry]:
        ids_list = list(ids)
        if not ids_list:
            return []

        result = await self.db.execute(
            select(InquiryTable).where(InquiryTable.id.in_(ids_list))
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def findByLaporanId(self, laporan_id: UUID) -> Iterable[Inquiry]:
        result = await self.db.execute(
            select(InquiryTable).where(InquiryTable.laporan_id == laporan_id)
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def findBySenderUserId(self, sender_user_id: UUID) -> Iterable[Inquiry]:
        result = await self.db.execute(
            select(InquiryTable).where(InquiryTable.sender_user_id == sender_user_id)
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(InquiryTable))
        return int(result.scalar_one())

    async def deleteById(self, id: UUID) -> None:
        await self.db.execute(delete(InquiryTable).where(InquiryTable.id == id))
        await self.db.commit()

    async def delete(self, entity: Inquiry) -> None:
        await self.deleteById(entity.id)

    async def deleteAllById(self, ids: Iterable[UUID]) -> None:
        ids_list = list(ids)
        if not ids_list:
            return

        await self.db.execute(delete(InquiryTable).where(InquiryTable.id.in_(ids_list)))
        await self.db.commit()

    async def deleteAll(self, entities: Iterable[Inquiry] | None = None) -> None:
        if entities is None:
            await self.db.execute(delete(InquiryTable))
            await self.db.commit()
            return

        entity_ids = [entity.id for entity in entities]
        await self.deleteAllById(entity_ids)
