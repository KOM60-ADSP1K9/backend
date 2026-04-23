"""
E2E tests for the Auth controller.

Endpoints under test
────────────────────
POST /auth/register
POST /auth/login
GET  /auth/verify-email
GET  /auth/me
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.e2e.helpers import (
    STAFF_EMAIL,
    STAFF_PASSWORD,
    VALID_DEPARTEMEN,
    VALID_EMAIL,
    VALID_FAKULTAS,
    VALID_NIM,
    VALID_PASSWORD,
    get_auth_header,
    seed_unverified_mahasiswa,
    seed_verified_mahasiswa,
    seed_verified_staff,
    seed_verified_staff_with_supervised_lokasi,
)

# ════════════════════════════════════════════════════════════════════
#  POST /auth/register
# ════════════════════════════════════════════════════════════════════


class TestRegister:
    """Registration endpoint tests."""

    @pytest.mark.asyncio
    @patch(
        "src.features.auth.auth_dependencies.SmtpEmailService.send_verification_email",
        new_callable=AsyncMock,
    )
    async def test_register_success(
        self, mock_email: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ):
        """A valid registration should return 201 with user data."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": VALID_EMAIL,
                "password": VALID_PASSWORD,
                "nim": VALID_NIM,
                "fakultas": VALID_FAKULTAS,
                "departemen": VALID_DEPARTEMEN,
            },
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["email"] == VALID_EMAIL
        assert body["data"]["role"] == "MAHASISWA"
        assert body["data"]["nim"] == VALID_NIM
        assert body["data"]["fakultas"] == VALID_FAKULTAS
        assert body["data"]["departemen"] == VALID_DEPARTEMEN
        mock_email.assert_awaited_once()

    @pytest.mark.asyncio
    @patch(
        "src.features.auth.auth_dependencies.SmtpEmailService.send_verification_email",
        new_callable=AsyncMock,
    )
    async def test_register_duplicate_email(
        self, mock_email: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ):
        """Registering with an already-taken email should return 409."""
        await seed_verified_mahasiswa(db_session)

        resp = await client.post(
            "/auth/register",
            json={
                "email": VALID_EMAIL,
                "password": VALID_PASSWORD,
                "nim": VALID_NIM,
                "fakultas": VALID_FAKULTAS,
                "departemen": VALID_DEPARTEMEN,
            },
        )

        assert resp.status_code == 409
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_register_invalid_email_domain(self, client: AsyncClient):
        """Only @apps.ipb.ac.id emails are allowed."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "user@gmail.com",
                "password": VALID_PASSWORD,
                "nim": VALID_NIM,
                "fakultas": VALID_FAKULTAS,
                "departemen": VALID_DEPARTEMEN,
            },
        )

        assert resp.status_code == 400
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Missing required fields should return 422 validation error."""
        resp = await client.post(
            "/auth/register",
            json={"email": VALID_EMAIL},
        )

        assert resp.status_code == 422
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_register_invalid_email_format(self, client: AsyncClient):
        """Malformed email should return 422."""
        resp = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": VALID_PASSWORD,
                "nim": VALID_NIM,
                "fakultas": VALID_FAKULTAS,
                "departemen": VALID_DEPARTEMEN,
            },
        )

        assert resp.status_code == 422


# ════════════════════════════════════════════════════════════════════
#  POST /auth/login
# ════════════════════════════════════════════════════════════════════


class TestLogin:
    """Login endpoint tests."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, db_session: AsyncSession):
        """A verified user should be able to login and receive a token."""
        await seed_verified_mahasiswa(db_session)

        resp = await client.post(
            "/auth/login",
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert "access_token" in body["data"]
        assert isinstance(body["data"]["access_token"], str)
        assert len(body["data"]["access_token"]) > 0

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Wrong password should return 401."""
        await seed_verified_mahasiswa(db_session)

        resp = await client.post(
            "/auth/login",
            json={"email": VALID_EMAIL, "password": "WrongPassword123"},
        )

        assert resp.status_code == 401
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with a non-existent email should return 401."""
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@apps.ipb.ac.id", "password": VALID_PASSWORD},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_login_unverified_email(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """An unverified user should not be able to login."""
        await seed_unverified_mahasiswa(db_session)

        resp = await client.post(
            "/auth/login",
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )

        assert resp.status_code == 401
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient):
        """Missing fields should return 422."""
        resp = await client.post("/auth/login", json={"email": VALID_EMAIL})

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_login_staff_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff users should also be able to login."""
        await seed_verified_staff(db_session)

        resp = await client.post(
            "/auth/login",
            json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD},
        )

        assert resp.status_code == 200
        assert "access_token" in resp.json()["data"]


# ════════════════════════════════════════════════════════════════════
#  GET /auth/verify-email
# ════════════════════════════════════════════════════════════════════


class TestVerifyEmail:
    """Email verification endpoint tests."""

    @pytest.mark.asyncio
    async def test_verify_email_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Valid verification token should verify the user's email."""
        user = await seed_unverified_mahasiswa(db_session)

        from src.infrastructure.services.jwt_token_service import JWTTokenService

        token = JWTTokenService().generate_verification_token(user.email)

        resp = await client.get(f"/auth/verify-email?token={token}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert (
            "berhasil" in body["message"].lower()
            or "success" in body["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        """An invalid token should return 401."""
        resp = await client.get("/auth/verify-email?token=invalid-token-here")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_email_already_verified(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Verifying an already-verified user should return 400."""
        user = await seed_verified_mahasiswa(db_session)

        from src.infrastructure.services.jwt_token_service import JWTTokenService

        token = JWTTokenService().generate_verification_token(user.email)

        resp = await client.get(f"/auth/verify-email?token={token}")

        assert resp.status_code == 400
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_verify_email_missing_token(self, client: AsyncClient):
        """Missing token query param should return 422."""
        resp = await client.get("/auth/verify-email")

        assert resp.status_code == 422


# ════════════════════════════════════════════════════════════════════
#  GET /auth/me
# ════════════════════════════════════════════════════════════════════


class TestMe:
    """Current user profile endpoint tests."""

    @pytest.mark.asyncio
    async def test_me_success(self, client: AsyncClient, db_session: AsyncSession):
        """Authenticated user should get their profile."""
        user = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(user)

        resp = await client.get("/auth/me", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["email"] == VALID_EMAIL
        assert body["data"]["role"] == "MAHASISWA"
        assert body["data"]["nim"] == VALID_NIM
        assert body["data"]["fakultas"] == VALID_FAKULTAS
        assert body["data"]["departemen"] == VALID_DEPARTEMEN
        assert body["data"]["supervised_at"] is None

    @pytest.mark.asyncio
    async def test_me_staff_profile(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A staff user should see STAFF role and nip in their profile."""
        user = await seed_verified_staff(db_session)  # staff didnt have lokasi
        headers = get_auth_header(user)

        resp = await client.get("/auth/me", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["role"] == "STAFF"
        assert body["data"]["supervised_at"] is None

    @pytest.mark.asyncio
    async def test_me_staff_with_supervised_lokasi(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff with lokasi_id should receive full lokasi details."""
        user, lokasi = await seed_verified_staff_with_supervised_lokasi(db_session)
        headers = get_auth_header(user)

        resp = await client.get("/auth/me", headers=headers)

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role"] == "STAFF"
        assert data["supervised_at"] == {
            "id": str(lokasi["id"]),
            "name": lokasi["name"],
            "latitude": lokasi["latitude"],
            "longitude": lokasi["longitude"],
        }

    @pytest.mark.asyncio
    async def test_me_no_token(self, client: AsyncClient):
        """Request without auth header should be rejected."""
        resp = await client.get("/auth/me")

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_invalid_token(self, client: AsyncClient):
        """Request with a bad token should return 401."""
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_after_login_flow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Full flow: seed → login → /me should work end-to-end."""
        await seed_verified_mahasiswa(db_session)

        login_resp = await client.post(
            "/auth/login",
            json={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        )
        token = login_resp.json()["data"]["access_token"]

        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert me_resp.status_code == 200
        assert me_resp.json()["data"]["email"] == VALID_EMAIL
        assert (
            me_resp.json()["data"]["supervised_at"] is None
        )  # mahasiswa should not have supervised_at lokasi
