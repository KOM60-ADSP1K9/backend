"""E2E tests for the Homepage controller.

Endpoints under test
────────────────────
GET /homepage/laporan – Get all laporan (authenticated)
"""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.laporan import LaporanHilang
from src.domain.entity.user import User, UserRole
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.infrastructure.tables.lokasi_table import LokasiTable
from tests.e2e.helpers import get_auth_header


async def seed_verified_user(
    db_session: AsyncSession,
    *,
    email: str,
    nim: str,
) -> User:
    user = User.New(
        email=email,
        hashed_password="hashed-password",
        role=UserRole.MAHASISWA,
        nim=nim,
        fakultas="FMIPA",
        departemen="Ilmu Komputer",
    )
    user.verify_email()
    return await UserRepository(db_session).save(user)


class TestGetAllHomepageLaporan:
    """GET /homepage/laporan – authenticated endpoint."""

    @pytest.mark.asyncio
    async def test_authenticated_user_should_see_all_reports_with_ownership_flag(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Homepage should return all reports and mark the current user's reports."""
        current_user = await seed_verified_user(
            db_session,
            email="home-owner@apps.ipb.ac.id",
            nim="G6401212001",
        )
        other_user = await seed_verified_user(
            db_session,
            email="home-other@apps.ipb.ac.id",
            nim="G6401212002",
        )
        headers = get_auth_header(current_user)

        lokasi = LokasiTable(
            name="Gedung Homepage",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()

        repository = LaporanRepository(db_session)
        await repository.save(
            LaporanHilang.New(
                photo="stub://lost-reports/mine.jpg",
                lost_at_location_id=lokasi.id,
                lost_at_date=date(2026, 4, 29),
                user_id=current_user.id,
            )
        )
        await repository.save(
            LaporanHilang.New(
                photo="stub://lost-reports/theirs.jpg",
                lost_at_location_id=lokasi.id,
                lost_at_date=date(2026, 4, 30),
                user_id=other_user.id,
            )
        )

        resp = await client.get("/homepage/laporan", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan fetched successfully"
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 2

        own_reports = [item for item in body["data"] if item["is_owned"]]
        foreign_reports = [item for item in body["data"] if not item["is_owned"]]

        assert len(own_reports) == 1
        assert len(foreign_reports) == 1
        assert own_reports[0]["photo"] == "stub://lost-reports/mine.jpg"
        assert foreign_reports[0]["photo"] == "stub://lost-reports/theirs.jpg"

        expected_keys = {
            "id",
            "type",
            "status",
            "photo",
            "lost_at_location_id",
            "lost_at_date",
            "found_at_location_id",
            "found_at_date",
            "created_at",
            "updated_at",
            "is_owned",
        }
        assert set(own_reports[0].keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_should_reject_request_without_auth(self, client: AsyncClient):
        """Unauthenticated requests should be rejected."""
        resp = await client.get("/homepage/laporan")

        assert resp.status_code in {401, 403}
        assert resp.json()["status"] == "error"
