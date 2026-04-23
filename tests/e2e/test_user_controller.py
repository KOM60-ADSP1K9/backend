"""
E2E tests for the User controller.

Endpoints under test
────────────────────
GET /users  – Get all users (Staff only)
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.e2e.helpers import (
    STAFF_EMAIL,
    VALID_EMAIL,
    get_auth_header,
    seed_verified_mahasiswa,
    seed_verified_staff,
    seed_verified_staff_with_supervised_lokasi,
)


class TestGetAllUsers:
    """GET /users – Staff-only endpoint."""

    @pytest.mark.asyncio
    async def test_get_all_users_as_staff(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff should receive a list of all users."""
        staff = await seed_verified_staff(db_session)
        await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(staff)

        resp = await client.get("/users", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 2

        emails = {u["email"] for u in body["data"]}
        assert STAFF_EMAIL in emails
        assert VALID_EMAIL in emails

    @pytest.mark.asyncio
    async def test_get_all_users_as_mahasiswa(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Mahasiswa should be forbidden from listing users."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.get("/users", headers=headers)

        assert resp.status_code == 403
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_get_all_users_no_auth(self, client: AsyncClient):
        """Unauthenticated request should be rejected."""
        resp = await client.get("/users")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_all_users_invalid_token(self, client: AsyncClient):
        """Invalid token should return 401."""
        resp = await client.get(
            "/users",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_all_users_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """When only the requesting staff exists, list should contain 1 user."""
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.get("/users", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["email"] == STAFF_EMAIL

    @pytest.mark.asyncio
    async def test_get_all_users_response_shape(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Verify the shape of each user object in the response."""
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.get("/users", headers=headers)

        assert resp.status_code == 200
        user_data = resp.json()["data"][0]

        expected_keys = {
            "id",
            "email",
            "role",
            "nim",
            "fakultas",
            "departemen",
            "nip",
            "lokasi_id",
            "lokasi",
            "email_verified_at",
            "created_at",
            "updated_at",
        }
        assert set(user_data.keys()) == expected_keys
        assert user_data["lokasi"] is None

    @pytest.mark.asyncio
    async def test_get_all_users_staff_with_supervised_lokasi(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff supervising a lokasi should expose full lokasi fields."""
        staff, lokasi = await seed_verified_staff_with_supervised_lokasi(db_session)
        headers = get_auth_header(staff)

        resp = await client.get("/users", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        staff_data = next(u for u in body["data"] if u["email"] == STAFF_EMAIL)

        assert staff_data["lokasi_id"] == str(lokasi["id"])
        assert staff_data["lokasi"] == {
            "id": str(lokasi["id"]),
            "name": lokasi["name"],
            "latitude": lokasi["latitude"],
            "longitude": lokasi["longitude"],
        }


class TestGetAllUsersIsolation:
    """Verify that tests are truly isolated – data from one test
    does not leak into another."""

    @pytest.mark.asyncio
    async def test_isolation_a(self, client: AsyncClient, db_session: AsyncSession):
        """Seed a mahasiswa and staff, expect exactly 2 users."""
        staff = await seed_verified_staff(db_session)
        await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(staff)

        resp = await client.get("/users", headers=headers)
        assert len(resp.json()["data"]) == 2

        # mahasiswa, lokasi_id is none
        mahasiswa_data = next(
            u for u in resp.json()["data"] if u["email"] == VALID_EMAIL
        )
        assert mahasiswa_data["lokasi_id"] is None
        assert mahasiswa_data["lokasi"] is None

    @pytest.mark.asyncio
    async def test_isolation_b(self, client: AsyncClient, db_session: AsyncSession):
        """Seed only a staff user, expect exactly 1 user
        (data from test_isolation_a must not be visible)."""
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.get("/users", headers=headers)
        assert len(resp.json()["data"]) == 1
