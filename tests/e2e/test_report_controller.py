"""E2E tests for the Report controller.

Endpoints under test
────────────────────
PATCH /reports/{laporan_id}/status – Update laporan status (owner or staff)
"""

from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.barang import Barang
from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan
from src.domain.entity.user import User
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.tables.lokasi_table import LokasiTable
from tests.e2e.helpers import (
    get_auth_header,
    seed_kategori_barang,
    seed_verified_mahasiswa,
    seed_verified_staff,
)


async def _seed_lost_laporan(
    db: AsyncSession,
    owner: User,
    status: LaporanStatus = LaporanStatus.ACTIVE,
) -> LaporanHilang:
    """Persist a lost laporan owned by the given user."""
    lokasi = LokasiTable(
        name="Gedung A",
        latitude=-6.554321,
        longitude=106.723456,
    )
    db.add(lokasi)
    await db.flush()
    kategori = await seed_kategori_barang(db)

    barang = Barang.New(
        name="KTP",
        description="Kartu tanda penduduk",
        photo="stub://lost-reports/lost-card.jpg",
        kategori_barang_id=kategori.id,
    )
    laporan = LaporanHilang.New(
        lost_at_location_id=lokasi.id,
        lost_at_date=date(2026, 4, 29),
        user_id=owner.id,
        status=LaporanStatus.ACTIVE,
    )
    laporan.addBarang(barang)
    laporan.status = status
    saved = await LaporanRepository(db).save(laporan)
    assert isinstance(saved, LaporanHilang)
    return saved


async def _seed_found_laporan(
    db: AsyncSession,
    owner: User,
    status: LaporanStatus = LaporanStatus.ACTIVE,
) -> LaporanTemuan:
    """Persist a found laporan owned by the given user."""
    lokasi = LokasiTable(
        name="Gedung B",
        latitude=-6.554321,
        longitude=106.723456,
    )
    db.add(lokasi)
    await db.flush()
    kategori = await seed_kategori_barang(db, name="Elektronik")

    barang = Barang.New(
        name="Dompet",
        description="Dompet kulit cokelat",
        photo="stub://lost-reports/found-card.jpg",
        kategori_barang_id=kategori.id,
    )
    laporan = LaporanTemuan.New(
        found_at_location_id=lokasi.id,
        found_at_date=date(2026, 4, 30),
        user_id=owner.id,
        status=LaporanStatus.ACTIVE,
    )
    laporan.addBarang(barang)
    laporan.status = status
    saved = await LaporanRepository(db).save(laporan)
    assert isinstance(saved, LaporanTemuan)
    return saved


class TestUpdateLaporanStatus:
    """PATCH /reports/{laporan_id}/status – owner or staff endpoint."""

    @pytest.mark.asyncio
    async def test_owner_can_mark_lost_laporan_as_self_resolved(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Lost laporan owner should be able to transition ACTIVE → self-resolved."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, mahasiswa)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.SELF_RESOLVED.value},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan status updated successfully"
        assert body["data"]["id"] == str(laporan.id)
        assert body["data"]["status"] == LaporanStatus.SELF_RESOLVED.value
        assert body["data"]["type"] == "hilang"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.SELF_RESOLVED

    @pytest.mark.asyncio
    async def test_owner_can_mark_found_laporan_as_resolved(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Found laporan owner should be able to transition ACTIVE → resolved."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_found_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.RESOLVED.value},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["status"] == LaporanStatus.RESOLVED.value

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.RESOLVED

    @pytest.mark.asyncio
    async def test_staff_non_owner_is_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff is not the laporan owner and must be forbidden."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_found_laporan(db_session, owner)
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.RESOLVED.value},
        )

        assert resp.status_code == 403
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_non_owner_mahasiswa_is_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A mahasiswa who does not own the laporan should be forbidden."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        from src.domain.entity.user import User as UserDomain, UserRole
        from src.infrastructure.repositories.user_repository import UserRepository

        intruder = UserDomain.New(
            email="intruder@apps.ipb.ac.id",
            hashed_password=owner.hashed_password,
            role=UserRole.MAHASISWA,
            nim="G6401211002",
            fakultas="FMIPA",
            departemen="Ilmu Komputer",
        )
        intruder.verify_email()
        saved_intruder = await UserRepository(db_session).save(intruder)
        headers = get_auth_header(saved_intruder)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.SELF_RESOLVED.value},
        )

        assert resp.status_code == 403
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing laporan should return 404."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{uuid4()}/status",
            headers=headers,
            json={"status": LaporanStatus.ACTIVE.value},
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Laporan tidak ditemukan"

    @pytest.mark.asyncio
    async def test_invalid_transition_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Transitioning from a terminal status should be rejected."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, mahasiswa, status=LaporanStatus.SELF_RESOLVED
        )
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.ACTIVE.value},
        )

        assert resp.status_code == 400
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.SELF_RESOLVED

    @pytest.mark.asyncio
    async def test_claim_pending_status_is_rejected_by_dto(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """CLAIM_PENDING is system-driven and rejected before usecase execution."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, mahasiswa)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.CLAIM_PENDING.value},
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Validation failed"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_draft_status_is_rejected_by_dto(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """DRAFT is the initial state and cannot be set via this endpoint."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, mahasiswa)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.DRAFT.value},
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Validation failed"

    @pytest.mark.asyncio
    async def test_returns_422_when_status_is_invalid(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """An unknown status value should fail validation."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, mahasiswa)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": "not-a-real-status"},
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Validation failed"

    @pytest.mark.asyncio
    async def test_returns_401_when_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Missing auth header should return 401/403."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, mahasiswa)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            json={"status": LaporanStatus.SELF_RESOLVED.value},
        )

        assert resp.status_code in (401, 403)
