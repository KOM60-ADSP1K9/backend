from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from src.domain.entity.i_lokasi_repository import ILokasiRepository
from src.domain.entity.lokasi import Lokasi
from src.infrastructure.tables import LokasiTable


class LokasiRepository(ILokasiRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> Iterable[Lokasi]:
        result = await self.db.execute(select(LokasiTable))
        rows = result.scalars().all()
        return [row.to_domain() for row in rows]
