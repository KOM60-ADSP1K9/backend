from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import i_staff_repository
from src.domain.entity.user import Staff, UserRole
from src.infrastructure.tables.user_table import UserTable


class StaffRepository(i_staff_repository.IStaffRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def find_by_email(self, email: str) -> Staff | None:
        result = await self.db.execute(
            select(UserTable).where(
                UserTable.email == email,
                UserTable.role == UserRole.STAFF,
            )
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_staff()

    async def save(self, entity: Staff) -> Staff:
        row = UserTable.from_domain(entity)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row.to_staff()

    async def update(self, entity: Staff) -> Staff:
        row = UserTable.from_domain(entity)
        merged = await self.db.merge(row)
        await self.db.commit()
        await self.db.refresh(merged)
        return merged.to_staff()

    async def saveAll(self, entities: Iterable[Staff]) -> Iterable[Staff]:
        rows = [UserTable.from_domain(entity) for entity in entities]
        self.db.add_all(rows)
        await self.db.commit()
        for row in rows:
            await self.db.refresh(row)
        return [row.to_staff() for row in rows]

    async def findById(self, id: UUID) -> Staff | None:
        result = await self.db.execute(
            select(UserTable).where(
                UserTable.id == id,
                UserTable.role == UserRole.STAFF,
            )
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_staff()

    async def existsById(self, id: UUID) -> bool:
        result = await self.db.execute(
            select(UserTable.id).where(
                UserTable.id == id,
                UserTable.role == UserRole.STAFF,
            )
        )
        return result.scalar_one_or_none() is not None

    async def findAll(self) -> Iterable[Staff]:
        result = await self.db.execute(
            select(UserTable).where(UserTable.role == UserRole.STAFF)
        )
        rows = result.scalars().all()
        return [row.to_staff() for row in rows]

    async def findAllById(self, ids: Iterable[UUID]) -> Iterable[Staff]:
        ids_list = list(ids)
        if not ids_list:
            return []

        result = await self.db.execute(
            select(UserTable).where(
                UserTable.id.in_(ids_list),
                UserTable.role == UserRole.STAFF,
            )
        )
        rows = result.scalars().all()
        return [row.to_staff() for row in rows]

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(UserTable)
            .where(UserTable.role == UserRole.STAFF)
        )
        return int(result.scalar_one())

    async def deleteById(self, id: UUID) -> None:
        await self.db.execute(
            delete(UserTable).where(
                UserTable.id == id,
                UserTable.role == UserRole.STAFF,
            )
        )
        await self.db.commit()

    async def delete(self, entity: Staff) -> None:
        await self.deleteById(entity.id)

    async def deleteAllById(self, ids: Iterable[UUID]) -> None:
        ids_list = list(ids)
        if not ids_list:
            return

        await self.db.execute(
            delete(UserTable).where(
                UserTable.id.in_(ids_list),
                UserTable.role == UserRole.STAFF,
            )
        )
        await self.db.commit()

    async def deleteAll(self, entities: Iterable[Staff] | None = None) -> None:
        if entities is None:
            await self.db.execute(
                delete(UserTable).where(UserTable.role == UserRole.STAFF)
            )
            await self.db.commit()
            return

        entity_ids = [entity.id for entity in entities]
        await self.deleteAllById(entity_ids)
