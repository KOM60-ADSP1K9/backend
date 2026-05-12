"""E2E tests for the Report controller.

Endpoints under test
────────────────────
PATCH /reports/{laporan_id}/status – Update laporan status (owner only)
PATCH /reports/{laporan_id}/barang – Update laporan barang (owner only)
PATCH /reports/{laporan_id}/details – Update laporan location and date (owner only)
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


class TestUpdateLaporanBarang:
    """PATCH /reports/{laporan_id}/barang – owner-only endpoint."""

    @pytest.mark.asyncio
    async def test_owner_can_update_barang_with_new_photo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Owner should be able to update barang name, description, photo, and kategori."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        new_kategori = await seed_kategori_barang(db_session, name="Identitas")
        original_photo = laporan.barang.photo if laporan.barang is not None else None
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={
                "barang_name": "KTM",
                "barang_description": "Kartu tanda mahasiswa",
                "kategori_barang_id": str(new_kategori.id),
            },
            files={"photo": ("new-card.jpg", b"new-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan barang updated successfully"
        assert body["data"]["barang"]["name"] == "KTM"
        assert body["data"]["barang"]["description"] == "Kartu tanda mahasiswa"
        assert body["data"]["barang"]["kategori_barang_id"] == str(new_kategori.id)
        assert body["data"]["barang"]["photo"] == (
            "https://placehold.co/600x400?text=stub://lost-reports/new-card.jpg"
        )

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.barang is not None
        assert reloaded.barang.name == "KTM"
        assert reloaded.barang.description == "Kartu tanda mahasiswa"
        assert reloaded.barang.kategori_barang_id == new_kategori.id
        assert reloaded.barang.photo == (
            "https://placehold.co/600x400?text=stub://lost-reports/new-card.jpg"
        )

        assert original_photo in client.storage_stub.deleted_urls

    @pytest.mark.asyncio
    async def test_owner_can_update_barang_without_photo(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Omitting photo should keep the existing photo intact."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        original_photo = laporan.barang.photo if laporan.barang is not None else None
        original_kategori = (
            laporan.barang.kategori_barang_id if laporan.barang is not None else None
        )
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={
                "barang_name": "KTM",
                "barang_description": "Kartu tanda mahasiswa",
                "kategori_barang_id": str(original_kategori),
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["barang"]["photo"] == original_photo

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.barang is not None
        assert reloaded.barang.photo == original_photo
        assert reloaded.barang.name == "KTM"

        assert client.storage_stub.deleted_urls == []

    @pytest.mark.asyncio
    async def test_non_owner_is_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A user who does not own the laporan should be forbidden."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={
                "barang_name": "Hacked",
                "barang_description": "Hacked",
                "kategori_barang_id": str(uuid4()),
            },
        )

        assert resp.status_code == 403
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.barang is not None
        assert reloaded.barang.name == "KTP"

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing laporan should return 404."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{uuid4()}/barang",
            headers=headers,
            data={
                "barang_name": "Whatever",
                "barang_description": "Whatever",
                "kategori_barang_id": str(uuid4()),
            },
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Laporan tidak ditemukan"

    @pytest.mark.asyncio
    async def test_cannot_update_barang_on_terminal_laporan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A laporan in a terminal status cannot have its barang updated."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.SELF_RESOLVED
        )
        kategori = laporan.barang.kategori_barang_id
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={
                "barang_name": "KTM",
                "barang_description": "Kartu tanda mahasiswa",
                "kategori_barang_id": str(kategori),
            },
        )

        assert resp.status_code == 400
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.barang is not None
        assert reloaded.barang.name == "KTP"

    @pytest.mark.asyncio
    async def test_returns_404_when_kategori_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing kategori barang should return 404 and not mutate the laporan."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={
                "barang_name": "KTM",
                "barang_description": "Kartu tanda mahasiswa",
                "kategori_barang_id": str(uuid4()),
            },
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Kategori barang tidak ditemukan"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.barang is not None
        assert reloaded.barang.name == "KTP"

    @pytest.mark.asyncio
    async def test_invalid_photo_type_returns_400(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A photo with a disallowed content type should fail validation."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={
                "barang_name": "KTM",
                "barang_description": "Kartu tanda mahasiswa",
                "kategori_barang_id": str(uuid4()),
            },
            files={"photo": ("bad.gif", b"fake-photo-bytes", "image/gif")},
        )

        assert resp.status_code == 400
        body = resp.json()
        assert body["status"] == "error"

    @pytest.mark.asyncio
    async def test_returns_422_when_required_fields_missing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Omitting barang_name should fail validation before usecase execution."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            headers=headers,
            data={"barang_description": "Kartu tanda mahasiswa"},
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
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/barang",
            data={
                "barang_name": "KTM",
                "barang_description": "Kartu tanda mahasiswa",
                "kategori_barang_id": str(uuid4()),
            },
        )

        assert resp.status_code in (401, 403)


class TestUpdateLaporanDetails:
    """PATCH /reports/{laporan_id}/details – owner-only endpoint."""

    @pytest.mark.asyncio
    async def test_owner_can_update_lost_laporan_details(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Owner of a hilang laporan should update lost_at_location_id and lost_at_date."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        new_lokasi = LokasiTable(
            name="Gedung C",
            latitude=-6.500000,
            longitude=106.700000,
        )
        db_session.add(new_lokasi)
        await db_session.flush()
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={
                "location_id": str(new_lokasi.id),
                "date": "2026-05-01",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan details updated successfully"
        assert body["data"]["lost_at_location_id"] == str(new_lokasi.id)
        assert body["data"]["lost_at_date"] == "2026-05-01"
        assert body["data"]["found_at_location_id"] is None
        assert body["data"]["found_at_date"] is None

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert isinstance(reloaded, LaporanHilang)
        assert reloaded.lost_at_location_id == new_lokasi.id
        assert reloaded.lost_at_date == date(2026, 5, 1)

    @pytest.mark.asyncio
    async def test_owner_can_update_found_laporan_details(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Owner of a temuan laporan should update found_at_location_id and found_at_date."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_found_laporan(db_session, owner)
        new_lokasi = LokasiTable(
            name="Gedung D",
            latitude=-6.510000,
            longitude=106.710000,
        )
        db_session.add(new_lokasi)
        await db_session.flush()
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={
                "location_id": str(new_lokasi.id),
                "date": "2026-05-02",
            },
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["found_at_location_id"] == str(new_lokasi.id)
        assert body["data"]["found_at_date"] == "2026-05-02"
        assert body["data"]["lost_at_location_id"] is None
        assert body["data"]["lost_at_date"] is None

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert isinstance(reloaded, LaporanTemuan)
        assert reloaded.found_at_location_id == new_lokasi.id
        assert reloaded.found_at_date == date(2026, 5, 2)

    @pytest.mark.asyncio
    async def test_non_owner_is_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A non-owner should be forbidden from updating laporan details."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        staff = await seed_verified_staff(db_session)
        new_lokasi = LokasiTable(
            name="Gedung E",
            latitude=-6.520000,
            longitude=106.720000,
        )
        db_session.add(new_lokasi)
        await db_session.flush()
        headers = get_auth_header(staff)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={
                "location_id": str(new_lokasi.id),
                "date": "2026-05-01",
            },
        )

        assert resp.status_code == 403
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert isinstance(reloaded, LaporanHilang)
        assert reloaded.lost_at_date == date(2026, 4, 29)

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing laporan should return 404."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.patch(
            f"/reports/{uuid4()}/details",
            headers=headers,
            json={
                "location_id": str(uuid4()),
                "date": "2026-05-01",
            },
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Laporan tidak ditemukan"

    @pytest.mark.asyncio
    async def test_returns_404_when_location_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing lokasi should return 404 and not mutate the laporan."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={
                "location_id": str(uuid4()),
                "date": "2026-05-01",
            },
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Lokasi tidak ditemukan"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert isinstance(reloaded, LaporanHilang)
        assert reloaded.lost_at_date == date(2026, 4, 29)

    @pytest.mark.asyncio
    async def test_cannot_update_details_on_terminal_laporan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A laporan in a terminal status cannot have its details updated."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.SELF_RESOLVED
        )
        new_lokasi = LokasiTable(
            name="Gedung F",
            latitude=-6.530000,
            longitude=106.730000,
        )
        db_session.add(new_lokasi)
        await db_session.flush()
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={
                "location_id": str(new_lokasi.id),
                "date": "2026-05-01",
            },
        )

        assert resp.status_code == 400
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert isinstance(reloaded, LaporanHilang)
        assert reloaded.lost_at_date == date(2026, 4, 29)

    @pytest.mark.asyncio
    async def test_returns_422_when_required_fields_missing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Omitting date should fail validation before usecase execution."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={"location_id": str(uuid4())},
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
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            json={
                "location_id": str(uuid4()),
                "date": "2026-05-01",
            },
        )

        assert resp.status_code in (401, 403)


class TestDeleteLaporan:
    """DELETE /reports/{laporan_id} – owner-only, draft-only endpoint."""

    @pytest.mark.asyncio
    async def test_owner_can_delete_draft_laporan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Owner should be able to delete a draft laporan and its photo."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.DRAFT
        )
        original_photo = laporan.barang.photo if laporan.barang is not None else None
        headers = get_auth_header(owner)

        resp = await client.delete(
            f"/reports/{laporan.id}",
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan deleted successfully"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is None

        assert original_photo in client.storage_stub.deleted_urls

    @pytest.mark.asyncio
    async def test_owner_can_delete_active_laporan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Owner should be able to delete an active laporan and its photo."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.ACTIVE
        )
        original_photo = laporan.barang.photo if laporan.barang is not None else None
        headers = get_auth_header(owner)

        resp = await client.delete(
            f"/reports/{laporan.id}",
            headers=headers,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan deleted successfully"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is None

        assert original_photo in client.storage_stub.deleted_urls

    @pytest.mark.asyncio
    async def test_non_owner_is_forbidden(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A non-owner must not delete another user's laporan."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.DRAFT
        )
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.delete(
            f"/reports/{laporan.id}",
            headers=headers,
        )

        assert resp.status_code == 403
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert client.storage_stub.deleted_urls == []

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing laporan should return 404."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.delete(
            f"/reports/{uuid4()}",
            headers=headers,
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Laporan tidak ditemukan"

    @pytest.mark.asyncio
    async def test_cannot_delete_non_draft_laporan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A laporan that is not in DRAFT status should not be deletable."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.CLAIM_PENDING
        )
        headers = get_auth_header(owner)

        resp = await client.delete(
            f"/reports/{laporan.id}",
            headers=headers,
        )

        assert resp.status_code == 400
        body = resp.json()
        assert body["status"] == "error"

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.CLAIM_PENDING
        assert client.storage_stub.deleted_urls == []

    @pytest.mark.asyncio
    async def test_returns_401_when_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Missing auth header should return 401/403."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.DRAFT
        )

        resp = await client.delete(f"/reports/{laporan.id}")

        assert resp.status_code in (401, 403)

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
