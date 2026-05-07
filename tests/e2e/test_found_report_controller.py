"""E2E tests for the Found Report controller.

Endpoints under test
────────────────────
POST /found-reports – Create found report (authenticated users)
"""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.laporan import LaporanStatus, LaporanType
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.tables.lokasi_table import LokasiTable
from tests.e2e.helpers import (
    get_auth_header,
    seed_kategori_barang,
    seed_verified_mahasiswa,
    seed_verified_staff_with_supervised_lokasi,
)


class TestCreateFoundReport:
    """POST /found-reports – authenticated endpoint."""

    @pytest.mark.asyncio
    async def test_mahasiswa_can_create_found_report(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Mahasiswa should be able to create a found report with an explicit lokasi."""
        mahasiswa = await seed_verified_mahasiswa(db_session)
        headers = get_auth_header(mahasiswa)

        lokasi = LokasiTable(
            name="Gedung B",
            latitude=-6.554321,
            longitude=106.723456,
        )
        db_session.add(lokasi)
        await db_session.flush()
        kategori = await seed_kategori_barang(db_session)

        resp = await client.post(
            "/found-reports",
            headers=headers,
            data={
                "barang_name": "Dompet",
                "barang_description": "Dompet kulit cokelat",
                "kategori_barang_id": str(kategori.id),
                "found_at_location_id": str(lokasi.id),
                "found_at_date": "2026-04-30",
            },
            files={"photo": ("found-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["message"] == "Found report created successfully"
        assert body["data"]["type"] == "temuan"
        assert body["data"]["status"] == "active"
        assert body["data"]["found_at_location_id"] == str(lokasi.id)
        assert body["data"]["found_at_date"] == "2026-04-30"
        assert body["data"]["barang"]["name"] == "Dompet"
        assert body["data"]["barang"]["description"] == "Dompet kulit cokelat"
        assert body["data"]["barang"]["kategori_barang_id"] == str(kategori.id)
        assert body["data"]["barang"]["photo"] == (
            "https://placehold.co/600x400?text=stub://lost-reports/found-card.jpg"
        )

        saved_reports = list(await LaporanRepository(db_session).findAll())
        assert len(saved_reports) == 1
        saved_report = saved_reports[0]
        assert saved_report.type is LaporanType.TEMUAN
        assert saved_report.status is LaporanStatus.ACTIVE
        assert saved_report.found_at_location_id == lokasi.id
        assert saved_report.found_at_date == date(2026, 4, 30)
        assert saved_report.barang is not None
        assert saved_report.barang.name == "Dompet"
        assert saved_report.barang.description == "Dompet kulit cokelat"
        assert saved_report.barang.kategori_barang_id == kategori.id
        assert saved_report.barang.photo == (
            "https://placehold.co/600x400?text=stub://lost-reports/found-card.jpg"
        )
        assert saved_report.user_id == mahasiswa.id

    @pytest.mark.asyncio
    async def test_staff_should_auto_use_supervised_location(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Staff should have the supervised lokasi assigned automatically."""
        staff, lokasi = await seed_verified_staff_with_supervised_lokasi(db_session)
        headers = get_auth_header(staff)

        decoy_lokasi = LokasiTable(
            name="Gedung Decoy",
            latitude=-6.551234,
            longitude=106.722222,
        )
        db_session.add(decoy_lokasi)
        await db_session.flush()
        kategori = await seed_kategori_barang(db_session)

        resp = await client.post(
            "/found-reports",
            headers=headers,
            data={
                "barang_name": "KTP",
                "barang_description": "Kartu tanda penduduk",
                "kategori_barang_id": str(kategori.id),
                "found_at_location_id": str(decoy_lokasi.id),
                "found_at_date": "2026-04-30",
            },
            files={"photo": ("found-card.jpg", b"fake-photo-bytes", "image/jpeg")},
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["found_at_location_id"] == str(lokasi["id"])
        assert body["data"]["barang"]["name"] == "KTP"
        assert body["data"]["barang"]["kategori_barang_id"] == str(kategori.id)

        saved_reports = list(await LaporanRepository(db_session).findAll())
        assert len(saved_reports) == 1
        saved_report = saved_reports[0]
        assert saved_report.found_at_location_id == lokasi["id"]
        assert saved_report.user_id == staff.id
        assert saved_report.barang is not None
        assert saved_report.barang.kategori_barang_id == kategori.id
