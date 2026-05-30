"""E2E tests for the Notification controller.

Endpoints under test
────────────────────
GET   /notifications            – List the current user's notifications.
PATCH /notifications/{id}/read  – Mark one of the current user's notifications read.

Notifications are produced as a side effect of creating an inquiry: the laporan
owner receives an ``inquiry_received`` notification and the inquiry sender
receives an ``inquiry_submitted`` confirmation.
"""

from datetime import date
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan
from src.domain.entity.user import User
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from tests.e2e.helpers import (
    get_auth_header,
    seed_other_verified_mahasiswa,
    seed_verified_mahasiswa,
)


@pytest.fixture(autouse=True)
def _mock_inquiry_notification_email():
    """Avoid hitting real SMTP when creating inquiries in e2e tests."""
    with patch(
        "src.infrastructure.services.smtp_email_service.SmtpEmailService.send_inquiry_notification",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


async def _seed_active_laporan_temuan(db: AsyncSession, owner_id) -> LaporanTemuan:
    laporan = LaporanTemuan.New(
        user_id=owner_id,
        found_at_date=date(2026, 4, 30),
        status=LaporanStatus.ACTIVE,
    )
    saved = await LaporanRepository(db).save(laporan)
    assert isinstance(saved, LaporanTemuan)
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


async def _create_claim_inquiry(client: AsyncClient, inquirer: User, laporan_id) -> str:
    resp = await client.post(
        "/inquiries/claim",
        headers=get_auth_header(inquirer),
        data=_claim_form(laporan_id),
        files=_claim_files(),
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def _seed_active_laporan_hilang(db: AsyncSession, owner_id) -> LaporanHilang:
    laporan = LaporanHilang.New(
        user_id=owner_id,
        lost_at_date=date(2026, 4, 30),
        status=LaporanStatus.ACTIVE,
    )
    saved = await LaporanRepository(db).save(laporan)
    assert isinstance(saved, LaporanHilang)
    return saved


async def _create_found_inquiry(client: AsyncClient, inquirer: User, laporan_id) -> str:
    resp = await client.post(
        "/inquiries/found",
        headers=get_auth_header(inquirer),
        data={
            "laporan_id": str(laporan_id),
            "message_content": "Saya menemukan barang ini",
            "finder_contact": "0812345678",
        },
        files={"photo": ("photo.jpg", b"fake-photo", "image/jpeg")},
    )
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


class TestListNotifications:
    """GET /notifications"""

    @pytest.mark.asyncio
    async def test_owner_can_see_own_notification(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        await _create_claim_inquiry(client, inquirer, laporan.id)

        resp = await client.get("/notifications", headers=get_auth_header(owner))

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["data"]["unread_count"] == 1
        notifications = body["data"]["notifications"]
        assert len(notifications) == 1
        assert notifications[0]["type"] == "inquiry_received"
        assert notifications[0]["recipient_user_id"] == str(owner.id)
        assert notifications[0]["laporan_id"] == str(laporan.id)
        assert notifications[0]["is_read"] is False

    @pytest.mark.asyncio
    async def test_sender_can_see_own_confirmation_notification(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        await _create_claim_inquiry(client, inquirer, laporan.id)

        resp = await client.get("/notifications", headers=get_auth_header(inquirer))

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["unread_count"] == 1
        notifications = body["data"]["notifications"]
        assert len(notifications) == 1
        assert notifications[0]["type"] == "inquiry_submitted"
        assert notifications[0]["recipient_user_id"] == str(inquirer.id)

    @pytest.mark.asyncio
    async def test_user_cannot_see_other_users_notifications(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)

        await _create_claim_inquiry(client, inquirer, laporan.id)

        # Owner's list only contains owner's notification, not the sender's.
        owner_resp = await client.get("/notifications", headers=get_auth_header(owner))
        inquirer_resp = await client.get(
            "/notifications", headers=get_auth_header(inquirer)
        )

        owner_ids = {n["id"] for n in owner_resp.json()["data"]["notifications"]}
        inquirer_ids = {n["id"] for n in inquirer_resp.json()["data"]["notifications"]}
        assert owner_ids.isdisjoint(inquirer_ids)
        for n in owner_resp.json()["data"]["notifications"]:
            assert n["recipient_user_id"] == str(owner.id)

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_user_without_notifications(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await seed_verified_mahasiswa(db_session)

        resp = await client.get("/notifications", headers=get_auth_header(user))

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["notifications"] == []
        assert body["data"]["unread_count"] == 0

    @pytest.mark.asyncio
    async def test_requires_authentication(self, client: AsyncClient):
        resp = await client.get("/notifications")
        assert resp.status_code == 401


class TestMarkNotificationRead:
    """PATCH /notifications/{id}/read"""

    @pytest.mark.asyncio
    async def test_user_can_mark_own_notification_read(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)
        await _create_claim_inquiry(client, inquirer, laporan.id)

        list_resp = await client.get("/notifications", headers=get_auth_header(owner))
        notification_id = list_resp.json()["data"]["notifications"][0]["id"]

        resp = await client.patch(
            f"/notifications/{notification_id}/read",
            headers=get_auth_header(owner),
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["is_read"] is True
        assert body["data"]["read_at"] is not None

        # Unread count drops to zero afterwards.
        after = await client.get("/notifications", headers=get_auth_header(owner))
        assert after.json()["data"]["unread_count"] == 0

    @pytest.mark.asyncio
    async def test_user_cannot_mark_other_users_notification_read(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)
        await _create_claim_inquiry(client, inquirer, laporan.id)

        # Grab the owner's notification id.
        owner_list = await client.get("/notifications", headers=get_auth_header(owner))
        owner_notification_id = owner_list.json()["data"]["notifications"][0]["id"]

        # The inquirer must not be able to mark it read.
        resp = await client.patch(
            f"/notifications/{owner_notification_id}/read",
            headers=get_auth_header(inquirer),
        )
        assert resp.status_code == 404

        # Owner's notification stays unread.
        after = await client.get("/notifications", headers=get_auth_header(owner))
        assert after.json()["data"]["unread_count"] == 1
        assert after.json()["data"]["notifications"][0]["is_read"] is False

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_notification(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await seed_verified_mahasiswa(db_session)

        resp = await client.patch(
            f"/notifications/{uuid4()}/read",
            headers=get_auth_header(user),
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_requires_authentication(self, client: AsyncClient):
        resp = await client.patch(f"/notifications/{uuid4()}/read")
        assert resp.status_code == 401


class TestInquiryStatusChangeNotifications:
    """Sender is notified when the laporan owner activates or rejects their inquiry."""

    async def _setup_proposed_claim(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> tuple[User, User, str]:
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_temuan(db_session, owner.id)
        inquiry_id = await _create_claim_inquiry(client, inquirer, laporan.id)
        return owner, inquirer, inquiry_id

    @pytest.mark.asyncio
    async def test_sender_notified_when_inquiry_accepted(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner, inquirer, inquiry_id = await self._setup_proposed_claim(
            client, db_session
        )

        resp = await client.patch(
            f"/inquiries/{inquiry_id}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )
        assert resp.status_code == 200

        listing = await client.get("/notifications", headers=get_auth_header(inquirer))
        notifications = listing.json()["data"]["notifications"]
        accepted = [n for n in notifications if n["type"] == "inquiry_accepted"]
        assert len(accepted) == 1
        assert accepted[0]["recipient_user_id"] == str(inquirer.id)
        assert accepted[0]["inquiry_id"] == inquiry_id
        assert accepted[0]["is_read"] is False

    @pytest.mark.asyncio
    async def test_sender_notified_when_inquiry_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner, inquirer, inquiry_id = await self._setup_proposed_claim(
            client, db_session
        )

        resp = await client.patch(
            f"/inquiries/{inquiry_id}/status",
            headers=get_auth_header(owner),
            json={"status": "rejected"},
        )
        assert resp.status_code == 200

        listing = await client.get("/notifications", headers=get_auth_header(inquirer))
        notifications = listing.json()["data"]["notifications"]
        rejected = [n for n in notifications if n["type"] == "inquiry_rejected"]
        assert len(rejected) == 1
        assert rejected[0]["recipient_user_id"] == str(inquirer.id)
        assert rejected[0]["inquiry_id"] == inquiry_id

    @pytest.mark.asyncio
    async def test_owner_not_notified_on_status_change(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner, inquirer, inquiry_id = await self._setup_proposed_claim(
            client, db_session
        )

        await client.patch(
            f"/inquiries/{inquiry_id}/status",
            headers=get_auth_header(owner),
            json={"status": "active"},
        )

        listing = await client.get("/notifications", headers=get_auth_header(owner))
        notifications = listing.json()["data"]["notifications"]
        # Owner only has the original inquiry_received notification; no status one.
        assert all(
            n["type"] not in ("inquiry_accepted", "inquiry_rejected")
            for n in notifications
        )

    async def _resolve_and_get_sender_notification(
        self, client, inquirer, owner, inquiry_id, status, notif_type
    ) -> dict:
        resp = await client.patch(
            f"/inquiries/{inquiry_id}/status",
            headers=get_auth_header(owner),
            json={"status": status},
        )
        assert resp.status_code == 200
        listing = await client.get("/notifications", headers=get_auth_header(inquirer))
        matches = [
            n
            for n in listing.json()["data"]["notifications"]
            if n["type"] == notif_type
        ]
        assert len(matches) == 1
        return matches[0]

    @pytest.mark.asyncio
    async def test_claim_accepted_message_is_claim_specific(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner, inquirer, inquiry_id = await self._setup_proposed_claim(
            client, db_session
        )
        notif = await self._resolve_and_get_sender_notification(
            client, inquirer, owner, inquiry_id, "active", "inquiry_accepted"
        )
        assert notif["message"] == "Pemilik laporan menerima klaim Anda"

    @pytest.mark.asyncio
    async def test_claim_rejected_message_is_claim_specific(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner, inquirer, inquiry_id = await self._setup_proposed_claim(
            client, db_session
        )
        notif = await self._resolve_and_get_sender_notification(
            client, inquirer, owner, inquiry_id, "rejected", "inquiry_rejected"
        )
        assert notif["message"] == "Pemilik laporan menolak klaim Anda"

    @pytest.mark.asyncio
    async def test_found_accepted_message_is_found_specific(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_hilang(db_session, owner.id)
        inquiry_id = await _create_found_inquiry(client, inquirer, laporan.id)

        notif = await self._resolve_and_get_sender_notification(
            client, inquirer, owner, inquiry_id, "active", "inquiry_accepted"
        )
        assert notif["message"] == "Pemilik laporan menerima bukti temuan barang"

    @pytest.mark.asyncio
    async def test_found_rejected_message_is_found_specific(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        owner = await seed_verified_mahasiswa(db_session)
        inquirer = await seed_other_verified_mahasiswa(db_session)
        laporan = await _seed_active_laporan_hilang(db_session, owner.id)
        inquiry_id = await _create_found_inquiry(client, inquirer, laporan.id)

        notif = await self._resolve_and_get_sender_notification(
            client, inquirer, owner, inquiry_id, "rejected", "inquiry_rejected"
        )
        assert notif["message"] == "Pemilik laporan menolak bukti temuan barang"
