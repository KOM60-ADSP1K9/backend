from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.i_mahasiswa_repository import IMahasiswaRepository
from src.domain.entity.user import Mahasiswa, UserRole
from src.infrastructure.tables.user_table import UserTable


class MahasiswaRepository(IMahasiswaRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def find_by_email(self, email: str) -> Mahasiswa | None:
        result = await self.db.execute(
            select(UserTable).where(
                UserTable.email == email,
                UserTable.role == UserRole.MAHASISWA,
            )
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_mahasiswa()

    async def save(self, entity: Mahasiswa) -> Mahasiswa:
        row = UserTable.from_domain(entity)
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row.to_mahasiswa()

    async def update(self, entity: Mahasiswa) -> Mahasiswa:
        row = UserTable.from_domain(entity)
        merged = await self.db.merge(row)
        await self.db.commit()
        await self.db.refresh(merged)
        return merged.to_mahasiswa()

    async def saveAll(self, entities: Iterable[Mahasiswa]) -> Iterable[Mahasiswa]:
        rows = [UserTable.from_domain(entity) for entity in entities]
        self.db.add_all(rows)
        await self.db.commit()
        for row in rows:
            await self.db.refresh(row)
        return [row.to_mahasiswa() for row in rows]

    async def findById(self, id: UUID) -> Mahasiswa | None:
        result = await self.db.execute(
            select(UserTable).where(
                UserTable.id == id,
                UserTable.role == UserRole.MAHASISWA,
            )
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_mahasiswa()

    async def existsById(self, id: UUID) -> bool:
        result = await self.db.execute(
            select(UserTable.id).where(
                UserTable.id == id,
                UserTable.role == UserRole.MAHASISWA,
            )
        )
        return result.scalar_one_or_none() is not None

    async def findAll(self) -> Iterable[Mahasiswa]:
        result = await self.db.execute(
            select(UserTable).where(UserTable.role == UserRole.MAHASISWA)
        )
        rows = result.scalars().all()
        return [row.to_mahasiswa() for row in rows]

    async def findAllById(self, ids: Iterable[UUID]) -> Iterable[Mahasiswa]:
        ids_list = list(ids)
        if not ids_list:
            return []

        result = await self.db.execute(
            select(UserTable).where(
                UserTable.id.in_(ids_list),
                UserTable.role == UserRole.MAHASISWA,
            )
        )
        rows = result.scalars().all()
        return [row.to_mahasiswa() for row in rows]

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(UserTable)
            .where(UserTable.role == UserRole.MAHASISWA)
        )
        return int(result.scalar_one())

    async def deleteById(self, id: UUID) -> None:
        await self.db.execute(
            delete(UserTable).where(
                UserTable.id == id,
                UserTable.role == UserRole.MAHASISWA,
            )
        )
        await self.db.commit()

    async def delete(self, entity: Mahasiswa) -> None:
        await self.deleteById(entity.id)

    async def deleteAllById(self, ids: Iterable[UUID]) -> None:
        ids_list = list(ids)
        if not ids_list:
            return

        await self.db.execute(
            delete(UserTable).where(
                UserTable.id.in_(ids_list),
                UserTable.role == UserRole.MAHASISWA,
            )
        )
        await self.db.commit()

    async def deleteAll(self, entities: Iterable[Mahasiswa] | None = None) -> None:
        if entities is None:
            await self.db.execute(
                delete(UserTable).where(UserTable.role == UserRole.MAHASISWA)
            )
            await self.db.commit()
            return

        entity_ids = [entity.id for entity in entities]
        await self.deleteAllById(entity_ids)
