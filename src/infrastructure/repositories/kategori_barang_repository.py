from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.i_kategori_barang_repository import IKategoriBarangRepository
from src.domain.entity.kategori_barang import KategoriBarang
from src.infrastructure.tables import KategoriBarangTable


class KategoriBarangRepository(IKategoriBarangRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> Iterable[KategoriBarang]:
        result = await self.db.execute(
            select(KategoriBarangTable).order_by(asc(KategoriBarangTable.name))
        )
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]

    async def find_by_id(self, kategori_id: UUID) -> KategoriBarang | None:
        result = await self.db.execute(
            select(KategoriBarangTable).where(KategoriBarangTable.id == kategori_id)
        )
        row = result.scalars().first()
        if row is None:
            return None
        return row.to_domain()
