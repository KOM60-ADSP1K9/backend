"""E2E tests for the Inquiry controller.

Endpoints under test
────────────────────
POST /inquiries/claim – Create ClaimInquiry on active LaporanTemuan.
POST /inquiries/found – Create FoundInquiry on active LaporanHilang.
"""

from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.inquiry import (
    ClaimInquiry,
    FoundInquiry,
    InquiryStatus,
)
from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from tests.e2e.helpers import (
    get_auth_header,
    seed_other_verified_mahasiswa,
    seed_verified_mahasiswa,
)


async def _seed_active_laporan_temuan(db: AsyncSession, owner_id) -> LaporanTemuan:
    laporan = LaporanTemuan.New(
        user_id=owner_id,
        found_at_date=date(2026, 4, 30),
        status=LaporanStatus.ACTIVE,
    )
    saved = await LaporanRepository(db).save(laporan)
    assert isinstance(saved, LaporanTemuan)
    return saved


async def _seed_active_laporan_hilang(db: AsyncSession, owner_id) -> LaporanHilang:
    laporan = LaporanHilang.New(
        user_id=owner_id,
        lost_at_date=date(2026, 4, 30),
        status=LaporanStatus.ACTIVE,
    )
    saved = await LaporanRepository(db).save(laporan)
    assert isinstance(saved, LaporanHilang)
    return saved


def _claim_form(laporan_id) -> dict:
    return {
        "laporan_id": str(laporan_id),
        "message_content": "Saya pemilik barang ini",
        "claimer_contact": "0812345678",
    }


def _claim_files() -> dict:
    return {
        "proof_of_ownership": ("proof.jpg", b"fake-proof", "image/jpeg"),
        "ktm": ("ktm.jpg", b"fake-ktm", "image/jpeg"),
    }


def _found_form(laporan_id) -> dict:
    return {
        "laporan_id": str(laporan_id),
        "message_content": "Saya menemukan barang ini",
        "finder_contact": "0812345678",
    }


def _found_files() -> dict:
    return {"photo": ("photo.jpg", b"fake-photo", "image/jpeg")}


class TestCreateClaimInquiry:
    """POST /inquiries/claim"""

    @pytest.mark.asyncio
    async def test_creates_claim_inquiry_on_active_laporan_temuan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(inquirer),
            data=_claim_form(laporan.id),
            files=_claim_files(),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["type"] == "claim"
        assert body["data"]["status"] == "proposed"
        assert body["data"]["laporan_id"] == str(laporan.id)
        assert body["data"]["sender_user_id"] == str(inquirer.id)
        assert body["data"]["claimer_contact"] == "0812345678"
        assert "stub://lost-reports/proof.jpg" in body["data"]["proof_of_ownership"]
        assert "stub://lost-reports/ktm.jpg" in body["data"]["ktm"]
        assert body["data"]["finder_contact"] is None
        assert body["data"]["photo"] is None

        saved = await LaporanRepository(db_session).findById(laporan.id)
        assert saved is not None
        assert len(saved.inquiries) == 1
        assert isinstance(saved.inquiries[0], ClaimInquiry)
        assert saved.inquiries[0].status == InquiryStatus.PROPOSED

    @pytest.mark.asyncio
    async def test_rejects_claim_inquiry_on_laporan_hilang(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_hilang(db_session, owner.id)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(inquirer),
            data=_claim_form(laporan.id),
            files=_claim_files(),
        )

        assert resp.status_code == 400
        assert "ClaimInquiry" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_when_laporan_not_active(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = LaporanTemuan.New(
            user_id=owner.id,
            found_at_date=date(2026, 4, 30),
            status=LaporanStatus.DRAFT,
        )
        saved_laporan = await LaporanRepository(db_session).save(laporan)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(inquirer),
            data=_claim_form(saved_laporan.id),
            files=_claim_files(),
        )

        assert resp.status_code == 400
        assert "active status" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_when_sender_is_owner(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(owner),
            data=_claim_form(laporan.id),
            files=_claim_files(),
        )

        assert resp.status_code == 400
        assert "own laporan" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_when_active_inquiry_already_exists(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        active_inquiry = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer.id,
            message_content="prev",
            claimer_contact="0800",
            proof_of_ownership="proof_url",
            ktm="ktm_url",
        )
        active_inquiry.status = InquiryStatus.ACTIVE
        laporan.inquiries.append(active_inquiry)
        await LaporanRepository(db_session).update(laporan)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(inquirer),
            data=_claim_form(laporan.id),
            files=_claim_files(),
        )

        assert resp.status_code == 400
        assert "active inquiry" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        inquirer = await seed_verified_mahasiswa(db_session)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(inquirer),
            data=_claim_form(uuid4()),
            files=_claim_files(),
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_rejects_invalid_photo_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        resp = await client.post(
            "/inquiries/claim",
            headers=get_auth_header(inquirer),
            data=_claim_form(laporan.id),
            files={
                "proof_of_ownership": ("proof.txt", b"text", "text/plain"),
                "ktm": ("ktm.jpg", b"k", "image/jpeg"),
            },
        )

        assert resp.status_code == 400
        assert "proof_of_ownership" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_requires_authentication(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        resp = await client.post(
            "/inquiries/claim",
            data=_claim_form(uuid4()),
            files=_claim_files(),
        )

        assert resp.status_code in (401, 403)


class TestCreateFoundInquiry:
    """POST /inquiries/found"""

    @pytest.mark.asyncio
    async def test_creates_found_inquiry_on_active_laporan_hilang(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_hilang(db_session, owner.id)

        resp = await client.post(
            "/inquiries/found",
            headers=get_auth_header(inquirer),
            data=_found_form(laporan.id),
            files=_found_files(),
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["type"] == "found"
        assert body["data"]["status"] == "proposed"
        assert body["data"]["laporan_id"] == str(laporan.id)
        assert body["data"]["sender_user_id"] == str(inquirer.id)
        assert body["data"]["finder_contact"] == "0812345678"
        assert "stub://lost-reports/photo.jpg" in body["data"]["photo"]
        assert body["data"]["claimer_contact"] is None
        assert body["data"]["proof_of_ownership"] is None
        assert body["data"]["ktm"] is None

        saved = await LaporanRepository(db_session).findById(laporan.id)
        assert saved is not None
        assert len(saved.inquiries) == 1
        assert isinstance(saved.inquiries[0], FoundInquiry)

    @pytest.mark.asyncio
    async def test_rejects_found_inquiry_on_laporan_temuan(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        resp = await client.post(
            "/inquiries/found",
            headers=get_auth_header(inquirer),
            data=_found_form(laporan.id),
            files=_found_files(),
        )

        assert resp.status_code == 400
        assert "FoundInquiry" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_when_laporan_not_active(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = LaporanHilang.New(
            user_id=owner.id,
            lost_at_date=date(2026, 4, 30),
            status=LaporanStatus.DRAFT,
        )
        saved_laporan = await LaporanRepository(db_session).save(laporan)

        resp = await client.post(
            "/inquiries/found",
            headers=get_auth_header(inquirer),
            data=_found_form(saved_laporan.id),
            files=_found_files(),
        )

        assert resp.status_code == 400
        assert "active status" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_when_sender_is_owner(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_hilang(db_session, owner.id)

        resp = await client.post(
            "/inquiries/found",
            headers=get_auth_header(owner),
            data=_found_form(laporan.id),
            files=_found_files(),
        )

        assert resp.status_code == 400
        assert "own laporan" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_returns_404_when_laporan_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        inquirer = await seed_verified_mahasiswa(db_session)

        resp = await client.post(
            "/inquiries/found",
            headers=get_auth_header(inquirer),
            data=_found_form(uuid4()),
            files=_found_files(),
        )

        assert resp.status_code == 404
