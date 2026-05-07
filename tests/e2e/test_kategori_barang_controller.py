"""E2E tests for the Kategori Barang controller.

Endpoints under test
────────────────────
GET /kategori-barang – Get all kategori barang (authenticated)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.tables.kategori_barang_table import KategoriBarangTable
from tests.e2e.helpers import get_auth_header, seed_verified_mahasiswa


async def seed_kategori_barang_rows(db_session: AsyncSession) -> None:
    """Insert sample kategori barang rows for retrieval tests."""
    db_session.add_all(
        [
            KategoriBarangTable(name="Electronics"),
            KategoriBarangTable(name="Books"),
            KategoriBarangTable(name="Bags"),
        ]
    )
    await db_session.commit()


class TestGetAllKategoriBarang:
    """GET /kategori-barang – authenticated endpoint."""

    @pytest.mark.asyncio
    async def test_should_return_all_kategori_barang_for_authenticated_user(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Authenticated user should receive all kategori barang."""
        user = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(user)
        await seed_kategori_barang_rows(db_session)

        resp = await client.get("/kategori-barang", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Kategori barang fetched successfully"
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 3

        names = [item["name"] for item in body["data"]]
        assert names == ["Bags", "Books", "Electronics"]

    @pytest.mark.asyncio
    async def test_should_not_return_kategori_barang_without_auth(
        self, client: AsyncClient
    ):
        """Request without token must be rejected."""
        resp = await client.get("/kategori-barang")

        assert resp.status_code in {401, 403}
        assert resp.json()["status"] == "error"
