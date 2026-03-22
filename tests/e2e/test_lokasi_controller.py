"""E2E tests for the Lokasi controller.

Endpoints under test
────────────────────
GET /locations – Get all locations (authenticated)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.tables.lokasi_table import LokasiTable
from tests.e2e.helpers import get_auth_header, seed_verified_mahasiswa


async def seed_locations(db_session: AsyncSession) -> None:
    """Insert sample location rows for retrieval tests."""
    db_session.add_all(
        [
            LokasiTable(name="A lokasi", latitude=-6.554321, longitude=106.723456),
            LokasiTable(name="Lokasi 1", latitude=-6.554321, longitude=106.723456),
            LokasiTable(name="Lokasi 2", latitude=-6.556789, longitude=106.725012),
        ],
    )
    await db_session.commit()


class TestGetAllLocations:
    """GET /locations – authenticated endpoint."""

    @pytest.mark.asyncio
    async def test_get_all_locations_authenticated_and_sorted_by_name(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Authenticated user should receive all stored locations."""
        user = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(user)
        await seed_locations(db_session)

        resp = await client.get("/locations", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Locations fetched successfully"
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 3

        names = [item["name"] for item in body["data"]]
        assert names == ["A lokasi", "Lokasi 1", "Lokasi 2"]

    @pytest.mark.asyncio
    async def test_get_all_locations_no_auth(self, client: AsyncClient):
        """Request without token must be rejected."""
        resp = await client.get("/locations")

        assert resp.status_code in {401, 403}
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_get_all_locations_invalid_token(self, client: AsyncClient):
        """Invalid token should return unauthorized."""
        resp = await client.get(
            "/locations",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert resp.status_code == 401
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_get_all_locations_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """If no locations exist, endpoint returns an empty list."""
        user = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(user)

        resp = await client.get("/locations", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"] == []
