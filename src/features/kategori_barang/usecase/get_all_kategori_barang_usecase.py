"""Usecase: Get all kategori barang."""

from collections.abc import Iterable

from src.domain.entity.i_kategori_barang_repository import IKategoriBarangRepository
from src.domain.entity.kategori_barang import KategoriBarang


class GetAllKategoriBarangResult:
    def __init__(self, kategori_barang: Iterable[KategoriBarang]) -> None:
        self.kategori_barang = kategori_barang


class GetAllKategoriBarangUsecase:
    """Get-all-kategori-barang use case with injected repository."""

    def __init__(self, kategori_barang_repository: IKategoriBarangRepository) -> None:
        self._kategori_barang_repository = kategori_barang_repository

    async def execute(self) -> GetAllKategoriBarangResult:
        """Return every kategori barang in the system."""
        kategori_barang = await self._kategori_barang_repository.get_all()
        return GetAllKategoriBarangResult(kategori_barang=kategori_barang)
