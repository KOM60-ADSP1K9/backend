"""E2E tests for the Inquiry controller.

Endpoints under test
────────────────────
POST  /inquiries/claim              – Create ClaimInquiry on active LaporanTemuan.
POST  /inquiries/found              – Create FoundInquiry on active LaporanHilang.
PATCH /inquiries/{inquiry_id}/status – Owner-only transition of inquiry status.
"""

from datetime import date
from unittest.mock import AsyncMock, patch
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


@pytest.fixture(autouse=True)
def _mock_inquiry_notification_email():
    """Avoid hitting real SMTP when creating inquiries in e2e tests."""
    with patch(
        "src.infrastructure.services.smtp_email_service.SmtpEmailService.send_inquiry_notification",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


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
        assert "active or pending status" in resp.json()["error"]

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
        assert "active or pending status" in resp.json()["error"]

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


async def _seed_laporan_temuan_with_claim_inquiry(
    db: AsyncSession,
    owner_id,
    inquirer_id,
    inquiry_status: InquiryStatus = InquiryStatus.PROPOSED,
) -> tuple[LaporanTemuan, ClaimInquiry]:
    laporan = await _seed_active_laporan_temuan(db, owner_id)
    inquiry = ClaimInquiry.New(
        laporan_id=laporan.id,
        sender_user_id=inquirer_id,
        message_content="Saya pemilik barang ini",
        claimer_contact="0812345678",
        proof_of_ownership="proof_url",
        ktm="ktm_url",
    )
    inquiry.status = inquiry_status
    laporan.inquiries.append(inquiry)
    if inquiry_status == InquiryStatus.PROPOSED:
        laporan.status = LaporanStatus.CLAIM_PENDING
    elif inquiry_status == InquiryStatus.ACTIVE:
        laporan.status = LaporanStatus.IN_PROGRESS
    saved = await LaporanRepository(db).update(laporan)
    assert isinstance(saved, LaporanTemuan)
    saved_inquiry = next(i for i in saved.inquiries if i.id == inquiry.id)
    assert isinstance(saved_inquiry, ClaimInquiry)
    return saved, saved_inquiry


async def _seed_laporan_hilang_with_found_inquiry(
    db: AsyncSession,
    owner_id,
    inquirer_id,
    inquiry_status: InquiryStatus = InquiryStatus.PROPOSED,
) -> tuple[LaporanHilang, FoundInquiry]:
    laporan = await _seed_active_laporan_hilang(db, owner_id)
    inquiry = FoundInquiry.New(
        laporan_id=laporan.id,
        sender_user_id=inquirer_id,
        message_content="Saya menemukan barang ini",
        finder_contact="0812345678",
        photo="photo_url",
    )
    inquiry.status = inquiry_status
    laporan.inquiries.append(inquiry)
    if inquiry_status == InquiryStatus.PROPOSED:
        laporan.status = LaporanStatus.FOUND_CLAIM_PENDING
    elif inquiry_status == InquiryStatus.ACTIVE:
        laporan.status = LaporanStatus.IN_PROGRESS
    saved = await LaporanRepository(db).update(laporan)
    assert isinstance(saved, LaporanHilang)
    saved_inquiry = next(i for i in saved.inquiries if i.id == inquiry.id)
    assert isinstance(saved_inquiry, FoundInquiry)
    return saved, saved_inquiry


class TestUpdateInquiryStatus:
    """PATCH /inquiries/{inquiry_id}/status"""

    @pytest.mark.asyncio
    async def test_owner_activates_proposed_claim_inquiry(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session, owner.id, inquirer.id
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["id"] == str(inquiry.id)
        assert body["data"]["status"] == "active"
        assert body["data"]["type"] == "claim"

        saved = await LaporanRepository(db_session).findById(inquiry.laporan_id)
        assert saved is not None
        saved_inquiry = next(i for i in saved.inquiries if i.id == inquiry.id)
        assert saved_inquiry.status == InquiryStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_owner_rejects_proposed_claim_inquiry(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session, owner.id, inquirer.id
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "rejected"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "rejected"

        saved = await LaporanRepository(db_session).findById(inquiry.laporan_id)
        assert saved is not None
        saved_inquiry = next(i for i in saved.inquiries if i.id == inquiry.id)
        assert saved_inquiry.status == InquiryStatus.REJECTED

    @pytest.mark.asyncio
    async def test_owner_rejects_active_claim_inquiry(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session,
            owner.id,
            inquirer.id,
            inquiry_status=InquiryStatus.ACTIVE,
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "rejected"},
        )

        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_owner_activates_proposed_found_inquiry(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_hilang_with_found_inquiry(
            db_session, owner.id, inquirer.id
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["status"] == "active"
        assert body["data"]["type"] == "found"

    @pytest.mark.asyncio
    async def test_rejects_activation_when_another_active_inquiry_exists(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan, proposed_inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session, owner.id, inquirer.id
        )

        other_active = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=inquirer.id,
            message_content="another",
            claimer_contact="0800",
            proof_of_ownership="proof2",
            ktm="ktm2",
        )
        other_active.status = InquiryStatus.ACTIVE
        laporan.inquiries.append(other_active)
        await LaporanRepository(db_session).update(laporan)

        resp = await client.patch(
            f"/inquiries/{proposed_inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )

        assert resp.status_code == 400
        assert "active inquiry" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_activation_when_inquiry_already_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session,
            owner.id,
            inquirer.id,
            inquiry_status=InquiryStatus.REJECTED,
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )

        assert resp.status_code == 400
        assert "proposed" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_reject_when_inquiry_already_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session,
            owner.id,
            inquirer.id,
            inquiry_status=InquiryStatus.REJECTED,
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "rejected"},
        )

        assert resp.status_code == 400
        assert "proposed or active" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_invalid_target_status_proposed(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session, owner.id, inquirer.id
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "proposed"},
        )

        assert resp.status_code == 400
        assert "Invalid target status" in resp.json()["error"]

    @pytest.mark.asyncio
    async def test_rejects_unknown_status_value(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session, owner.id, inquirer.id
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(owner),
            json={"status": "closed"},
        )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_forbids_non_owner(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        _, inquiry = await _seed_laporan_temuan_with_claim_inquiry(
            db_session, owner.id, inquirer.id
        )

        resp = await client.patch(
            f"/inquiries/{inquiry.id}/status",
            headers=get_auth_header(inquirer),
            json={"status": "active"},
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_returns_404_when_inquiry_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)

        resp = await client.patch(
            f"/inquiries/{uuid4()}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_requires_authentication(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        resp = await client.patch(
            f"/inquiries/{uuid4()}/status",
            json={"status": "active"},
        )

        assert resp.status_code in (401, 403)
