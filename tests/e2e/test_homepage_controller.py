"""E2E tests for the Homepage controller.

Endpoints under test
────────────────────
GET /homepage/laporan – Get all laporan (authenticated)
"""

from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.barang import Barang
from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan
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
        mine = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 29),
            user_id=current_user.id,
        )
        mine.addBarang(
            Barang.New(
                name="KTP",
                description="Kartu tanda penduduk",
                photo="stub://lost-reports/mine.jpg",
            )
        )
        await repository.save(mine)

        found_by_me = LaporanTemuan.New(
            found_at_location_id=lokasi.id,
            found_at_date=date(2026, 4, 30),
            user_id=current_user.id,
        )
        found_by_me.addBarang(
            Barang.New(
                name="Tas",
                description="Tas laptop hitam",
                photo="stub://found-reports/mine-found.jpg",
            )
        )
        await repository.save(found_by_me)

        theirs = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 30),
            user_id=other_user.id,
        )
        theirs.addBarang(
            Barang.New(
                name="Dompet",
                description="Dompet kulit cokelat",
                photo="stub://lost-reports/theirs.jpg",
            )
        )
        await repository.save(theirs)

        resp = await client.get("/homepage/laporan", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan fetched successfully"
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 3

        own_reports = [item for item in body["data"] if item["is_owned"]]
        foreign_reports = [item for item in body["data"] if not item["is_owned"]]

        assert len(own_reports) == 2
        assert len(foreign_reports) == 1

        lost_report = next(item for item in own_reports if item["type"] == "hilang")
        found_report = next(item for item in own_reports if item["type"] == "temuan")

        assert lost_report["barang"]["name"] == "KTP"
        assert lost_report["barang"]["photo"] == "stub://lost-reports/mine.jpg"
        assert lost_report["status"] == "draft"

        assert any(item["type"] == "temuan" for item in own_reports)
        assert found_report["barang"]["name"] == "Tas"
        assert found_report["barang"]["photo"] == "stub://found-reports/mine-found.jpg"
        assert found_report["status"] == "draft"
        assert foreign_reports[0]["barang"]["name"] == "Dompet"
        assert foreign_reports[0]["barang"]["photo"] == "stub://lost-reports/theirs.jpg"

        expected_keys = {
            "id",
            "type",
            "status",
            "lost_at_location_id",
            "lost_at_date",
            "found_at_location_id",
            "found_at_date",
            "created_at",
            "updated_at",
            "barang",
            "is_owned",
        }
        assert set(own_reports[0].keys()) == expected_keys
        assert set(own_reports[0]["barang"].keys()) == {
            "id",
            "name",
            "description",
            "photo",
            "created_at",
            "updated_at",
        }

    @pytest.mark.asyncio
    async def test_should_reject_request_without_auth(self, client: AsyncClient):
        """Unauthenticated requests should be rejected."""
        resp = await client.get("/homepage/laporan")

        assert resp.status_code in {401, 403}
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_should_filter_reports_by_type_status_and_both(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Homepage should support filtering by type, status, and both together."""
        current_user = await seed_verified_user(
            db_session,
            email="home-filter@apps.ipb.ac.id",
            nim="G6401212003",
        )
        other_user = await seed_verified_user(
            db_session,
            email="home-filter-other@apps.ipb.ac.id",
            nim="G6401212004",
        )
        headers = get_auth_header(current_user)

        lokasi = LokasiTable(
            name="Gedung Filter",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()

        repository = LaporanRepository(db_session)

        mine = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 29),
            user_id=current_user.id,
        )
        mine.status = LaporanStatus.ACTIVE
        mine.addBarang(
            Barang.New(
                name="Kartu Mahasiswa",
                description="KTM biru",
                photo="stub://lost-reports/active.jpg",
            )
        )
        await repository.save(mine)

        found_by_me = LaporanTemuan.New(
            found_at_location_id=lokasi.id,
            found_at_date=date(2026, 4, 30),
            user_id=current_user.id,
        )
        found_by_me.addBarang(
            Barang.New(
                name="Tas",
                description="Tas laptop hitam",
                photo="stub://found-reports/closed.jpg",
            )
        )
        await repository.save(found_by_me)

        theirs = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 30),
            user_id=other_user.id,
        )
        theirs.addBarang(
            Barang.New(
                name="Dompet",
                description="Dompet kulit cokelat",
                photo="stub://lost-reports/other-closed.jpg",
            )
        )
        await repository.save(theirs)

        type_resp = await client.get(
            "/homepage/laporan",
            headers=headers,
            params={"type": "hilang"},
        )
        assert type_resp.status_code == 200
        type_body = type_resp.json()
        assert len(type_body["data"]) == 2
        assert {item["type"] for item in type_body["data"]} == {"hilang"}

        status_resp = await client.get(
            "/homepage/laporan",
            headers=headers,
            params={"status": "active"},
        )
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        assert len(status_body["data"]) == 1
        assert {item["status"] for item in status_body["data"]} == {"active"}

        combined_resp = await client.get(
            "/homepage/laporan",
            headers=headers,
            params={"type": "hilang", "status": "active"},
        )
        assert combined_resp.status_code == 200
        combined_body = combined_resp.json()
        assert len(combined_body["data"]) == 1
        assert combined_body["data"][0]["type"] == "hilang"
        assert combined_body["data"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_should_page_reports_with_page_and_limit(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Homepage should skip earlier rows when page is advanced."""
        current_user = await seed_verified_user(
            db_session,
            email="home-page@apps.ipb.ac.id",
            nim="G6401212005",
        )
        headers = get_auth_header(current_user)

        lokasi = LokasiTable(
            name="Gedung Page",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()

        repository = LaporanRepository(db_session)
        base_time = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)

        oldest = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 27),
            user_id=current_user.id,
        )
        oldest.created_at = base_time
        oldest.updated_at = base_time
        oldest.addBarang(
            Barang.New(
                name="Kunci",
                description="Kunci kos",
                photo="stub://lost-reports/oldest.jpg",
            )
        )
        await repository.save(oldest)

        middle = LaporanTemuan.New(
            found_at_location_id=lokasi.id,
            found_at_date=date(2026, 4, 28),
            user_id=current_user.id,
        )
        middle.created_at = base_time + timedelta(minutes=1)
        middle.updated_at = base_time + timedelta(minutes=1)
        middle.addBarang(
            Barang.New(
                name="Dompet",
                description="Dompet hitam",
                photo="stub://found-reports/middle.jpg",
            )
        )
        await repository.save(middle)

        newest = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 29),
            user_id=current_user.id,
        )
        newest.created_at = base_time + timedelta(minutes=2)
        newest.updated_at = base_time + timedelta(minutes=2)
        newest.addBarang(
            Barang.New(
                name="Jaket",
                description="Jaket abu-abu",
                photo="stub://lost-reports/newest.jpg",
            )
        )
        await repository.save(newest)

        resp = await client.get(
            "/homepage/laporan",
            headers=headers,
            params={"limit": 1, "page": 2},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["data"]) == 1
        assert body["data"][0]["barang"]["name"] == "Dompet"
