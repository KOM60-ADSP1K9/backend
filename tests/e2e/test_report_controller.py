"""E2E tests for the Report controller.

Endpoints under test
────────────────────
GET   /reports/{laporan_id}         – Get laporan detail with all inquiries
PATCH /reports/{laporan_id}/status – Update laporan status (owner only)
PATCH /reports/{laporan_id}/barang – Update laporan barang (owner only)
PATCH /reports/{laporan_id}/details – Update laporan location and date (owner only)
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.barang import Barang
from src.domain.entity.inquiry import ClaimInquiry, FoundInquiry, InquiryStatus
from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan
from src.domain.entity.user import User
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.tables.lokasi_table import LokasiTable
from tests.e2e.helpers import (
    get_auth_header,
    seed_kategori_barang,
    seed_other_verified_mahasiswa,
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
    async def test_owner_can_mark_active_laporan_as_closed(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Owner should be able to transition ACTIVE → closed (cancel)."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.CLOSED.value},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["status"] == LaporanStatus.CLOSED.value

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.CLOSED

    @pytest.mark.asyncio
    async def test_owner_can_mark_in_progress_temuan_as_resolved(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Temuan owner should be able to transition IN_PROGRESS → resolved after claim accepted."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_found_laporan(
            db_session, owner, status=LaporanStatus.IN_PROGRESS
        )
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
    async def test_owner_can_mark_in_progress_hilang_as_resolved(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Hilang owner should be able to transition IN_PROGRESS → resolved after found inquiry accepted."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.IN_PROGRESS
        )
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
    async def test_owner_can_mark_found_claim_pending_as_resolved(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Hilang owner should be able to transition FOUND_CLAIM_PENDING → resolved."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.FOUND_CLAIM_PENDING
        )
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
    async def test_owner_can_cancel_found_claim_pending_back_to_active(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Hilang owner should be able to transition FOUND_CLAIM_PENDING → active (cancel)."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(
            db_session, owner, status=LaporanStatus.FOUND_CLAIM_PENDING
        )
        headers = get_auth_header(owner)

        resp = await client.patch(
            f"/reports/{laporan.id}/status",
            headers=headers,
            json={"status": LaporanStatus.ACTIVE.value},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["status"] == LaporanStatus.ACTIVE.value

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert reloaded.status is LaporanStatus.ACTIVE

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

    @pytest.mark.asyncio
    async def test_returns_422_when_date_is_in_the_future(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Future date should fail PastDate validation and not mutate the laporan."""
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)
        new_lokasi = LokasiTable(
            name="Gedung Future",
            latitude=-6.540000,
            longitude=106.740000,
        )
        db_session.add(new_lokasi)
        await db_session.flush()
        headers = get_auth_header(owner)

        future_date = (date.today() + timedelta(days=1)).isoformat()
        resp = await client.patch(
            f"/reports/{laporan.id}/details",
            headers=headers,
            json={
                "location_id": str(new_lokasi.id),
                "date": future_date,
            },
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Validation failed"
        assert any(
            error["field"] == "body.date"
            for error in body["errors"]
            if isinstance(error, dict)
        )

        reloaded = await LaporanRepository(db_session).findById(laporan.id)
        assert reloaded is not None
        assert isinstance(reloaded, LaporanHilang)
        assert reloaded.lost_at_date == date(2026, 4, 29)


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


class TestGetLaporanDetail:
    """GET /reports/{laporan_id} – laporan detail with all inquiries."""

    @pytest.mark.asyncio
    async def test_owner_sees_is_owned_true_and_empty_inquiries(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)

        resp = await client.get(
            f"/reports/{laporan.id}",
            headers=get_auth_header(owner),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Laporan detail fetched successfully"
        data = body["data"]
        assert data["id"] == str(laporan.id)
        assert data["type"] == "hilang"
        assert data["status"] == "active"
        assert data["is_owned"] is True
        assert data["user"]["email"] == owner.email
        assert data["barang"]["name"] == "KTP"
        assert data["barang"]["kategori_barang"] is not None
        assert data["inquiries"] == []

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
            "inquiries",
        }
        assert set(data.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_non_owner_sees_is_owned_false(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        viewer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)

        resp = await client.get(
            f"/reports/{laporan.id}",
            headers=get_auth_header(viewer),
        )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["is_owned"] is False
        assert data["user"]["email"] == owner.email

    @pytest.mark.asyncio
    async def test_includes_claim_inquiry_with_sender_and_is_owned_flags(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_found_laporan(db_session, owner)

        inquiry = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer.id,
            message_content="Saya pemilik barang ini",
            claimer_contact="0812345678",
            proof_of_ownership="stub://proof.jpg",
            ktm="stub://ktm.jpg",
        )
        laporan.inquiries.append(inquiry)
        await LaporanRepository(db_session).update(laporan)

        owner_resp = await client.get(
            f"/reports/{laporan.id}",
            headers=get_auth_header(owner),
        )
        assert owner_resp.status_code == 200
        owner_data = owner_resp.json()["data"]
        assert owner_data["is_owned"] is True
        assert len(owner_data["inquiries"]) == 1

        owner_inq = owner_data["inquiries"][0]
        assert owner_inq["id"] == str(inquiry.id)
        assert owner_inq["type"] == "claim"
        assert owner_inq["status"] == "proposed"
        assert owner_inq["sender_user_id"] == str(inquirer.id)
        assert owner_inq["sender"]["email"] == inquirer.email
        assert owner_inq["claimer_contact"] == "0812345678"
        assert owner_inq["proof_of_ownership"] == "stub://proof.jpg"
        assert owner_inq["ktm"] == "stub://ktm.jpg"
        assert owner_inq["finder_contact"] is None
        assert owner_inq["photo"] is None
        # owner is NOT the sender of this inquiry
        assert owner_inq["is_owned"] is False

        inquirer_resp = await client.get(
            f"/reports/{laporan.id}",
            headers=get_auth_header(inquirer),
        )
        assert inquirer_resp.status_code == 200
        inquirer_data = inquirer_resp.json()["data"]
        # inquirer does NOT own the laporan
        assert inquirer_data["is_owned"] is False
        # inquirer DOES own the inquiry they sent
        assert inquirer_data["inquiries"][0]["is_owned"] is True

    @pytest.mark.asyncio
    async def test_includes_found_inquiry_with_polymorphic_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)

        inquiry = FoundInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer.id,
            message_content="Saya menemukan barang ini",
            finder_contact="0899999999",
            photo="stub://found-photo.jpg",
        )
        laporan.inquiries.append(inquiry)
        await LaporanRepository(db_session).update(laporan)

        resp = await client.get(
            f"/reports/{laporan.id}",
            headers=get_auth_header(owner),
        )
        assert resp.status_code == 200
        inq = resp.json()["data"]["inquiries"][0]
        assert inq["type"] == "found"
        assert inq["finder_contact"] == "0899999999"
        assert inq["photo"] == "stub://found-photo.jpg"
        assert inq["claimer_contact"] is None
        assert inq["proof_of_ownership"] is None
        assert inq["ktm"] is None
        assert inq["sender"]["email"] == inquirer.email

        expected_inquiry_keys = {
            "id",
            "type",
            "status",
            "laporan_id",
            "sender_user_id",
            "sender",
            "message_content",
            "send_date",
            "claimer_contact",
            "proof_of_ownership",
            "ktm",
            "finder_contact",
            "photo",
            "created_at",
            "updated_at",
            "is_owned",
        }
        assert set(inq.keys()) == expected_inquiry_keys

    @pytest.mark.asyncio
    async def test_returns_all_inquiries_across_statuses(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer_a = await seed_other_verified_mahasiswa(db_session)
        inquirer_b = await seed_other_verified_mahasiswa(
            db_session,
            email="inquirer-b@apps.ipb.ac.id",
            nim="G6401299999",
        )
        laporan = await _seed_found_laporan(db_session, owner)

        proposed = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer_a.id,
            message_content="proposed",
            claimer_contact="0800000001",
            proof_of_ownership="stub://p1.jpg",
            ktm="stub://k1.jpg",
        )
        active = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer_a.id,
            message_content="active",
            claimer_contact="0800000002",
            proof_of_ownership="stub://p2.jpg",
            ktm="stub://k2.jpg",
        )
        active.status = InquiryStatus.ACTIVE
        rejected = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer_b.id,
            message_content="rejected",
            claimer_contact="0800000003",
            proof_of_ownership="stub://p3.jpg",
            ktm="stub://k3.jpg",
        )
        rejected.status = InquiryStatus.REJECTED
        laporan.inquiries.extend([proposed, active, rejected])
        await LaporanRepository(db_session).update(laporan)

        resp = await client.get(
            f"/reports/{laporan.id}",
            headers=get_auth_header(owner),
        )

        assert resp.status_code == 200
        inquiries = resp.json()["data"]["inquiries"]
        assert len(inquiries) == 3
        statuses = {i["status"] for i in inquiries}
        assert statuses == {"proposed", "active", "rejected"}
        senders = {i["sender_user_id"] for i in inquiries}
        assert senders == {str(inquirer_a.id), str(inquirer_b.id)}
        # owner never sent any inquiry
        assert all(i["is_owned"] is False for i in inquiries)

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_missing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        viewer = await seed_verified_mahasiswa(db_session)

        resp = await client.get(
            f"/reports/{uuid4()}",
            headers=get_auth_header(viewer),
        )

        assert resp.status_code == 404
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_returns_401_when_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_lost_laporan(db_session, owner)

        resp = await client.get(f"/reports/{laporan.id}")

        assert resp.status_code in (401, 403)
