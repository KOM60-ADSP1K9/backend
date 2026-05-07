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
from tests.e2e.helpers import get_auth_header, seed_kategori_barang


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
        kategori = await seed_kategori_barang(db_session)

        repository = LaporanRepository(db_session)
        mine = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 29),
            user_id=current_user.id,
        )
        mine.status = LaporanStatus.ACTIVE
        mine.addBarang(
            Barang.New(
                name="KTP",
                description="Kartu tanda penduduk",
                photo="stub://lost-reports/mine.jpg",
                kategori_barang_id=kategori.id,
            )
        )
        await repository.save(mine)

        found_by_me = LaporanTemuan.New(
            found_at_location_id=lokasi.id,
            found_at_date=date(2026, 4, 30),
            user_id=current_user.id,
        )
        found_by_me.status = LaporanStatus.ACTIVE
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
        theirs.status = LaporanStatus.ACTIVE
        theirs.addBarang(
            Barang.New(
                name="Dompet",
                description="Dompet kulit cokelat",
                photo="stub://lost-reports/theirs.jpg",
            )
        )
        await repository.save(theirs)

        hidden_draft = LaporanTemuan.New(
            found_at_location_id=lokasi.id,
            found_at_date=date(2026, 4, 30),
            user_id=other_user.id,
        )
        hidden_draft.addBarang(
            Barang.New(
                name="Topi",
                description="Topi hitam",
                photo="stub://found-reports/draft-hidden.jpg",
            )
        )
        await repository.save(hidden_draft)

        resp = await client.get("/homepage/laporan", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan fetched successfully"
        assert isinstance(body["data"], list)
        assert len(body["data"]) == 3
        assert all(item["status"] != "draft" for item in body["data"])

        own_reports = [item for item in body["data"] if item["is_owned"]]
        foreign_reports = [item for item in body["data"] if not item["is_owned"]]

        assert len(own_reports) == 2
        assert len(foreign_reports) == 1

        lost_report = next(item for item in own_reports if item["type"] == "hilang")
        found_report = next(item for item in own_reports if item["type"] == "temuan")

        assert lost_report["barang"]["name"] == "KTP"
        assert lost_report["barang"]["photo"] == "stub://lost-reports/mine.jpg"
        assert lost_report["status"] == "active"

        assert any(item["type"] == "temuan" for item in own_reports)
        assert found_report["barang"]["name"] == "Tas"
        assert found_report["barang"]["photo"] == "stub://found-reports/mine-found.jpg"
        assert found_report["status"] == "active"
        assert foreign_reports[0]["barang"]["name"] == "Dompet"
        assert foreign_reports[0]["barang"]["photo"] == "stub://lost-reports/theirs.jpg"
        assert foreign_reports[0]["status"] == "active"

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
            "user",
            "is_owned",
        }
        assert set(lost_report.keys()) == expected_keys
        assert set(lost_report["barang"].keys()) == {
            "id",
            "name",
            "description",
            "photo",
            "kategori_barang_id",
            "kategori_barang",
            "created_at",
            "updated_at",
        }
        assert lost_report["barang"]["kategori_barang_id"] == str(kategori.id)
        assert lost_report["barang"]["kategori_barang"] == {
            "id": str(kategori.id),
            "name": "Dokumen",
        }
        assert set(lost_report["user"].keys()) == {"email", "nim", "nip"}
        assert lost_report["user"]["email"] == current_user.email
        assert lost_report["user"]["nim"] == current_user.nim
        assert lost_report["user"]["nip"] is None
        assert foreign_reports[0]["user"]["email"] == other_user.email

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
        theirs.status = LaporanStatus.ACTIVE
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
        assert all(item["status"] == "active" for item in type_body["data"])
        assert {item["user"]["email"] for item in type_body["data"]} == {
            current_user.email,
            other_user.email,
        }

        status_resp = await client.get(
            "/homepage/laporan",
            headers=headers,
            params={"status": "active"},
        )
        assert status_resp.status_code == 200
        status_body = status_resp.json()
        assert len(status_body["data"]) == 2
        assert {item["status"] for item in status_body["data"]} == {"active"}
        assert {item["user"]["email"] for item in status_body["data"]} == {
            current_user.email,
            other_user.email,
        }

        combined_resp = await client.get(
            "/homepage/laporan",
            headers=headers,
            params={"type": "hilang", "status": "active"},
        )
        assert combined_resp.status_code == 200
        combined_body = combined_resp.json()
        assert len(combined_body["data"]) == 2
        assert combined_body["data"][0]["type"] == "hilang"
        assert all(item["status"] == "active" for item in combined_body["data"])
        assert {item["user"]["email"] for item in combined_body["data"]} == {
            current_user.email,
            other_user.email,
        }

    @pytest.mark.asyncio
    async def test_should_return_only_current_users_reports_on_my_laporan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """My laporan endpoint should only return laporan created by the caller."""
        current_user = await seed_verified_user(
            db_session,
            email="home-my@apps.ipb.ac.id",
            nim="G6401212005",
        )
        other_user = await seed_verified_user(
            db_session,
            email="home-my-other@apps.ipb.ac.id",
            nim="G6401212006",
        )
        headers = get_auth_header(current_user)

        lokasi = LokasiTable(
            name="Gedung My",
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

        mine_two = LaporanTemuan.New(
            found_at_location_id=lokasi.id,
            found_at_date=date(2026, 4, 30),
            user_id=current_user.id,
        )
        mine_two.addBarang(
            Barang.New(
                name="Tas",
                description="Tas laptop hitam",
                photo="stub://found-reports/mine-two.jpg",
            )
        )
        await repository.save(mine_two)

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

        resp = await client.get("/homepage/laporan/me", headers=headers)

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan fetched successfully"
        assert len(body["data"]) == 2
        assert all(item["is_owned"] for item in body["data"])
        assert {item["user"]["email"] for item in body["data"]} == {
            current_user.email,
        }
        assert {item["barang"]["name"] for item in body["data"]} == {
            "KTP",
            "Tas",
        }
        assert {item["barang"]["name"] for item in body["data"]} != {"Dompet"}

    @pytest.mark.asyncio
    async def test_should_filter_and_page_my_laporan_with_query_params(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """My laporan endpoint should support type, status, page, and limit."""
        current_user = await seed_verified_user(
            db_session,
            email="home-my-query@apps.ipb.ac.id",
            nim="G6401212007",
        )
        other_user = await seed_verified_user(
            db_session,
            email="home-my-query-other@apps.ipb.ac.id",
            nim="G6401212008",
        )
        headers = get_auth_header(current_user)

        lokasi = LokasiTable(
            name="Gedung My Query",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()

        repository = LaporanRepository(db_session)
        base_time = datetime(2026, 4, 1, 10, 0, tzinfo=timezone.utc)

        newest = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 29),
            user_id=current_user.id,
        )
        newest.status = LaporanStatus.ACTIVE
        newest.created_at = base_time + timedelta(minutes=2)
        newest.updated_at = base_time + timedelta(minutes=2)
        newest.addBarang(
            Barang.New(
                name="KTP",
                description="Kartu tanda penduduk",
                photo="stub://lost-reports/my-query-newest.jpg",
            )
        )
        await repository.save(newest)

        older = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 28),
            user_id=current_user.id,
        )
        older.status = LaporanStatus.ACTIVE
        older.created_at = base_time + timedelta(minutes=1)
        older.updated_at = base_time + timedelta(minutes=1)
        older.addBarang(
            Barang.New(
                name="Jaket",
                description="Jaket abu-abu",
                photo="stub://lost-reports/my-query-older.jpg",
            )
        )
        await repository.save(older)

        other = LaporanHilang.New(
            lost_at_location_id=lokasi.id,
            lost_at_date=date(2026, 4, 30),
            user_id=other_user.id,
        )
        other.status = LaporanStatus.ACTIVE
        other.created_at = base_time + timedelta(minutes=3)
        other.updated_at = base_time + timedelta(minutes=3)
        other.addBarang(
            Barang.New(
                name="Dompet",
                description="Dompet kulit cokelat",
                photo="stub://lost-reports/other-query.jpg",
            )
        )
        await repository.save(other)

        page_one_resp = await client.get(
            "/homepage/laporan/me",
            headers=headers,
            params={"type": "hilang", "status": "active", "page": 1, "limit": 1},
        )
        assert page_one_resp.status_code == 200
        page_one_body = page_one_resp.json()
        assert len(page_one_body["data"]) == 1
        assert page_one_body["data"][0]["barang"]["name"] == "KTP"
        assert page_one_body["data"][0]["type"] == "hilang"
        assert page_one_body["data"][0]["status"] == "active"
        assert page_one_body["data"][0]["user"]["email"] == current_user.email
        assert page_one_body["data"][0]["is_owned"] is True

        page_two_resp = await client.get(
            "/homepage/laporan/me",
            headers=headers,
            params={"type": "hilang", "status": "active", "page": 2, "limit": 1},
        )
        assert page_two_resp.status_code == 200
        page_two_body = page_two_resp.json()
        assert len(page_two_body["data"]) == 1
        assert page_two_body["data"][0]["barang"]["name"] == "Jaket"
        assert page_two_body["data"][0]["type"] == "hilang"
        assert page_two_body["data"][0]["status"] == "active"
        assert page_two_body["data"][0]["user"]["email"] == current_user.email
        assert page_two_body["data"][0]["is_owned"] is True

        page_three_resp = await client.get(
            "/homepage/laporan/me",
            headers=headers,
            params={"type": "hilang", "status": "active", "page": 3, "limit": 1},
        )
        assert page_three_resp.status_code == 200
        assert page_three_resp.json()["data"] == []

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
        oldest.status = LaporanStatus.ACTIVE
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
        middle.status = LaporanStatus.ACTIVE
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
        newest.status = LaporanStatus.ACTIVE
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
