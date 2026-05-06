"""E2E tests for the Lost Report controller.

Endpoints under test
────────────────────
POST /lost-reports – Create lost report (Mahasiswa only)
"""

from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.laporan import LaporanStatus, LaporanType
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.tables.lokasi_table import LokasiTable
from tests.e2e.helpers import (
    get_auth_header,
    seed_verified_mahasiswa,
    seed_verified_staff,
)


class TestCreateLostReport:
    """POST /lost-reports – mahasiswa-only endpoint."""

    @pytest.mark.asyncio
    async def test_mahasiswa_can_create_lost_report(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Mahasiswa should be able to create a lost report with a photo upload."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        lokasi = LokasiTable(
            name="Gedung A",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()

        resp = await client.post(
            "/lost-reports",
            headers=headers,
            data={
                "barang_name": "KTP",
                "barang_description": "Kartu tanda penduduk",
                "lost_at_location_id": str(lokasi.id),
                "lost_at_date": "2026-04-29",
            },
            files={"photo": ("lost-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Lost report created successfully"
        assert body["data"]["type"] == "hilang"
        assert body["data"]["status"] == "draft"
        assert body["data"]["barang"]["name"] == "KTP"
        assert body["data"]["barang"]["description"] == "Kartu tanda penduduk"
        assert body["data"]["barang"]["photo"] == (
            "https://placehold.co/600x400?text=stub://lost-reports/lost-card.jpg"
        )
        assert body["data"]["lost_at_location_id"] == str(lokasi.id)
        assert body["data"]["lost_at_date"] == "2026-04-29"
        assert set(body["data"].keys()) == {
            "id",
            "type",
            "status",
            "lost_at_location_id",
            "lost_at_date",
            "created_at",
            "updated_at",
            "barang",
        }

        saved_reports = list(await LaporanRepository(db_session).findAll())
        assert len(saved_reports) == 1
        saved_report = saved_reports[0]
        assert saved_report.type is LaporanType.HILANG
        assert saved_report.status is LaporanStatus.DRAFT
        assert saved_report.barang is not None
        assert saved_report.barang.name == "KTP"
        assert saved_report.barang.description == "Kartu tanda penduduk"
        assert saved_report.barang.photo == (
            "https://placehold.co/600x400?text=stub://lost-reports/lost-card.jpg"
        )
        assert saved_report.user_id == mahasiswa.id
        assert saved_report.lost_at_date == date(2026, 4, 29)

    @pytest.mark.asyncio
    async def test_staff_cannot_create_lost_report(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff should be forbidden from creating lost reports."""
        staff = await seed_verified_staff(db_session)
        headers = get_auth_header(staff)

        resp = await client.post(
            "/lost-reports",
            headers=headers,
            data={
                "barang_name": "KTP",
                "barang_description": "Kartu tanda penduduk",
                "lost_at_location_id": str(uuid4()),
                "lost_at_date": "2026-04-29",
            },
            files={"photo": ("lost-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 403
        assert resp.json()["status"] == "error"

    @pytest.mark.asyncio
    async def test_should_fail_when_location_id_does_not_exist(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A missing lokasi should return 404 and not create a report."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.post(
            "/lost-reports",
            headers=headers,
            data={
                "barang_name": "KTP",
                "barang_description": "Kartu tanda penduduk",
                "lost_at_location_id": str(uuid4()),
                "lost_at_date": "2026-04-29",
            },
            files={"photo": ("lost-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 404
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Lokasi tidak ditemukan"
        assert body["errors"] == ["Lokasi tidak ditemukan"]

        saved_reports = list(await LaporanRepository(db_session).findAll())
        assert saved_reports == []

    @pytest.mark.asyncio
    async def test_should_fail_when_location_id_is_missing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Omitting lokasi id should fail validation before usecase execution."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        resp = await client.post(
            "/lost-reports",
            headers=headers,
            data={
                "barang_name": "KTP",
                "barang_description": "Kartu tanda penduduk",
                "lost_at_date": "2026-04-29",
            },
            files={"photo": ("lost-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Validation failed"
        assert any(
            error["field"] == "body.lost_at_location_id"
            for error in body["errors"]
            if isinstance(error, dict)
        )

        saved_reports = list(await LaporanRepository(db_session).findAll())
        assert saved_reports == []

    @pytest.mark.asyncio
    async def test_should_fail_when_date_is_missing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Omitting lost_at_date should fail validation before usecase execution."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        lokasi = LokasiTable(
            name="Gedung B",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()

        resp = await client.post(
            "/lost-reports",
            headers=headers,
            data={
                "barang_name": "KTP",
                "barang_description": "Kartu tanda penduduk",
                "lost_at_location_id": str(lokasi.id),
            },
            files={"photo": ("lost-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error"] == "Validation failed"
        assert any(
            error["field"] == "body.lost_at_date"
            for error in body["errors"]
            if isinstance(error, dict)
        )

        saved_reports = list(await LaporanRepository(db_session).findAll())
        assert saved_reports == []
