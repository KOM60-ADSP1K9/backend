"""Unit tests for Laporan inquiry aggregate domain logic."""

from uuid import uuid4

import pytest

from src.domain.entity.inquiry import (
    ClaimInquiry,
    FoundInquiry,
    InquiryStatus,
)
from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan


def _make_claim_inquiry(
    laporan_id, status: InquiryStatus = InquiryStatus.PROPOSED
) -> ClaimInquiry:
    inquiry = ClaimInquiry.New(
        laporan_id=laporan_id,
        sender_user_id=uuid4(),
        message_content="msg",
        claimer_contact="contact",
        proof_of_ownership="proof",
        ktm="ktm",
    )
    inquiry.status = status
    return inquiry


def _make_found_inquiry(
    laporan_id, status: InquiryStatus = InquiryStatus.PROPOSED
) -> FoundInquiry:
    inquiry = FoundInquiry.New(
        laporan_id=laporan_id,
        sender_user_id=uuid4(),
        message_content="msg",
        finder_contact="contact",
        photo="photo",
    )
    inquiry.status = status
    return inquiry


def _active_temuan() -> LaporanTemuan:
    laporan = LaporanTemuan.New(user_id=uuid4())
    laporan.mark_as_active()
    return laporan


def _active_hilang() -> LaporanHilang:
    laporan = LaporanHilang.New(user_id=uuid4())
    laporan.mark_as_active()
    return laporan


def _claim_pending_temuan() -> LaporanTemuan:
    laporan = _active_temuan()
    laporan.mark_as_claim_pending()
    return laporan


def _found_claim_pending_hilang() -> LaporanHilang:
    laporan = _active_hilang()
    laporan.mark_as_found_claim_pending()
    return laporan


class TestLaporanTemuanAddInquiry:
    def test_accepts_claim_inquiry_when_no_existing(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id)

        result = laporan.add_inquiry(inquiry)

        assert result is inquiry
        assert inquiry in laporan.inquiries

    def test_rejects_found_inquiry(self) -> None:
        laporan = _active_temuan()
        wrong = _make_found_inquiry(laporan.id)

        with pytest.raises(ValueError, match="ClaimInquiry"):
            laporan.add_inquiry(wrong)

        assert wrong not in laporan.inquiries

    def test_rejects_when_active_inquiry_exists(self) -> None:
        laporan = _active_temuan()
        existing_active = _make_claim_inquiry(laporan.id, InquiryStatus.ACTIVE)
        laporan.inquiries.append(existing_active)
        new_inquiry = _make_claim_inquiry(laporan.id)

        with pytest.raises(ValueError, match="active inquiry"):
            laporan.add_inquiry(new_inquiry)

        assert new_inquiry not in laporan.inquiries

    def test_allows_when_only_proposed_inquiries_exist(self) -> None:
        laporan = _active_temuan()
        existing_proposed = _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED)
        laporan.inquiries.append(existing_proposed)
        new_inquiry = _make_claim_inquiry(laporan.id)

        result = laporan.add_inquiry(new_inquiry)

        assert result is new_inquiry
        assert new_inquiry in laporan.inquiries

    def test_allows_when_only_rejected_inquiries_exist(self) -> None:
        laporan = _active_temuan()
        existing_rejected = _make_claim_inquiry(laporan.id, InquiryStatus.REJECTED)
        laporan.inquiries.append(existing_rejected)
        new_inquiry = _make_claim_inquiry(laporan.id)

        result = laporan.add_inquiry(new_inquiry)

        assert result is new_inquiry
        assert new_inquiry in laporan.inquiries

    def test_rejects_when_active_mixed_with_others(self) -> None:
        laporan = _active_temuan()
        laporan.inquiries.extend(
            [
                _make_claim_inquiry(laporan.id, InquiryStatus.REJECTED),
                _make_claim_inquiry(laporan.id, InquiryStatus.ACTIVE),
                _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED),
            ]
        )
        new_inquiry = _make_claim_inquiry(laporan.id)

        with pytest.raises(ValueError, match="active inquiry"):
            laporan.add_inquiry(new_inquiry)

    def test_rejects_when_laporan_status_not_active(self) -> None:
        laporan = LaporanTemuan.New(user_id=uuid4())  # status=DRAFT
        new_inquiry = _make_claim_inquiry(laporan.id)

        with pytest.raises(ValueError, match="active or pending status"):
            laporan.add_inquiry(new_inquiry)

    def test_rejects_when_sender_is_owner(self) -> None:
        laporan = _active_temuan()
        inquiry = ClaimInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=laporan.user_id,
            message_content="msg",
            claimer_contact="contact",
            proof_of_ownership="proof",
            ktm="ktm",
        )

        with pytest.raises(ValueError, match="own laporan"):
            laporan.add_inquiry(inquiry)


class TestLaporanHilangAddInquiry:
    def test_accepts_found_inquiry_when_no_existing(self) -> None:
        laporan = _active_hilang()
        inquiry = _make_found_inquiry(laporan.id)

        result = laporan.add_inquiry(inquiry)

        assert result is inquiry
        assert inquiry in laporan.inquiries

    def test_rejects_claim_inquiry(self) -> None:
        laporan = _active_hilang()
        wrong = _make_claim_inquiry(laporan.id)

        with pytest.raises(ValueError, match="FoundInquiry"):
            laporan.add_inquiry(wrong)

    def test_rejects_when_active_inquiry_exists(self) -> None:
        laporan = _active_hilang()
        existing_active = _make_found_inquiry(laporan.id, InquiryStatus.ACTIVE)
        laporan.inquiries.append(existing_active)
        new_inquiry = _make_found_inquiry(laporan.id)

        with pytest.raises(ValueError, match="active inquiry"):
            laporan.add_inquiry(new_inquiry)

    def test_allows_when_only_proposed_inquiries_exist(self) -> None:
        laporan = _active_hilang()
        existing_proposed = _make_found_inquiry(laporan.id, InquiryStatus.PROPOSED)
        laporan.inquiries.append(existing_proposed)
        new_inquiry = _make_found_inquiry(laporan.id)

        result = laporan.add_inquiry(new_inquiry)

        assert result is new_inquiry

    def test_allows_when_only_rejected_inquiries_exist(self) -> None:
        laporan = _active_hilang()
        existing_rejected = _make_found_inquiry(laporan.id, InquiryStatus.REJECTED)
        laporan.inquiries.append(existing_rejected)
        new_inquiry = _make_found_inquiry(laporan.id)

        result = laporan.add_inquiry(new_inquiry)

        assert result is new_inquiry

    def test_rejects_when_laporan_status_not_active(self) -> None:
        laporan = LaporanHilang.New(user_id=uuid4())  # status=DRAFT
        new_inquiry = _make_found_inquiry(laporan.id)

        with pytest.raises(ValueError, match="active or pending status"):
            laporan.add_inquiry(new_inquiry)

    def test_rejects_when_sender_is_owner(self) -> None:
        laporan = _active_hilang()
        inquiry = FoundInquiry.New(
            laporan_id=laporan.id,
            sender_user_id=laporan.user_id,
            message_content="msg",
            finder_contact="contact",
            photo="photo",
        )

        with pytest.raises(ValueError, match="own laporan"):
            laporan.add_inquiry(inquiry)


class TestLaporanMakeInquiryActive:
    def test_promotes_proposed_to_active(self) -> None:
        laporan = _claim_pending_temuan()
        inquiry = _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED)
        laporan.inquiries.append(inquiry)

        result = laporan.make_inquiry_active(inquiry)

        assert result is inquiry
        assert inquiry.status == InquiryStatus.ACTIVE
        assert laporan.status == LaporanStatus.IN_PROGRESS

    def test_rejects_wrong_inquiry_type(self) -> None:
        laporan = _active_hilang()
        wrong = _make_claim_inquiry(laporan.id)

        with pytest.raises(ValueError, match="FoundInquiry"):
            laporan.make_inquiry_active(wrong)

    def test_rejects_inquiry_not_belonging_to_laporan(self) -> None:
        laporan = _active_temuan()
        other_laporan_id = uuid4()
        inquiry = _make_claim_inquiry(other_laporan_id)

        with pytest.raises(ValueError, match="does not belong"):
            laporan.make_inquiry_active(inquiry)

    def test_rejects_when_inquiry_not_proposed(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id, InquiryStatus.REJECTED)
        laporan.inquiries.append(inquiry)

        with pytest.raises(ValueError, match="proposed"):
            laporan.make_inquiry_active(inquiry)

    def test_rejects_when_another_active_exists(self) -> None:
        laporan = _active_temuan()
        active = _make_claim_inquiry(laporan.id, InquiryStatus.ACTIVE)
        new = _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED)
        laporan.inquiries.extend([active, new])

        with pytest.raises(ValueError, match="already an active"):
            laporan.make_inquiry_active(new)

        assert new.status == InquiryStatus.PROPOSED

    def test_self_in_existing_list_does_not_block(self) -> None:
        laporan = _claim_pending_temuan()
        inquiry = _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED)
        other_rejected = _make_claim_inquiry(laporan.id, InquiryStatus.REJECTED)
        laporan.inquiries.extend([inquiry, other_rejected])

        result = laporan.make_inquiry_active(inquiry)

        assert result.status == InquiryStatus.ACTIVE
        assert laporan.status == LaporanStatus.IN_PROGRESS


class TestLaporanRejectInquiry:
    def test_rejects_from_proposed(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED)

        result = laporan.reject_inquiry(inquiry)

        assert result is inquiry
        assert inquiry.status == InquiryStatus.REJECTED

    def test_rejects_from_active(self) -> None:
        laporan = _active_hilang()
        inquiry = _make_found_inquiry(laporan.id, InquiryStatus.ACTIVE)

        result = laporan.reject_inquiry(inquiry)

        assert inquiry.status == InquiryStatus.REJECTED
        assert result is inquiry

    def test_cannot_reject_already_rejected(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id, InquiryStatus.REJECTED)

        with pytest.raises(ValueError, match="proposed or active"):
            laporan.reject_inquiry(inquiry)

    def test_rejects_wrong_inquiry_type(self) -> None:
        laporan = _active_temuan()
        wrong = _make_found_inquiry(laporan.id, InquiryStatus.PROPOSED)

        with pytest.raises(ValueError, match="ClaimInquiry"):
            laporan.reject_inquiry(wrong)

    def test_rejects_inquiry_not_belonging_to_laporan(self) -> None:
        laporan = _active_hilang()
        other_laporan_id = uuid4()
        inquiry = _make_found_inquiry(other_laporan_id, InquiryStatus.PROPOSED)

        with pytest.raises(ValueError, match="does not belong"):
            laporan.reject_inquiry(inquiry)


class TestLaporanStatusOnInquiryTransition:
    def test_add_inquiry_transitions_active_to_claim_pending(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id)

        laporan.add_inquiry(inquiry)

        assert laporan.status == LaporanStatus.CLAIM_PENDING

    def test_add_inquiry_transitions_active_to_found_claim_pending(self) -> None:
        laporan = _active_hilang()
        inquiry = _make_found_inquiry(laporan.id)

        laporan.add_inquiry(inquiry)

        assert laporan.status == LaporanStatus.FOUND_CLAIM_PENDING

    def test_add_inquiry_allowed_when_already_claim_pending(self) -> None:
        laporan = _active_temuan()
        first = _make_claim_inquiry(laporan.id)
        laporan.add_inquiry(first)
        second = _make_claim_inquiry(laporan.id)

        laporan.add_inquiry(second)

        assert laporan.status == LaporanStatus.CLAIM_PENDING
        assert second in laporan.inquiries

    def test_add_inquiry_allowed_when_already_found_claim_pending(self) -> None:
        laporan = _active_hilang()
        first = _make_found_inquiry(laporan.id)
        laporan.add_inquiry(first)
        second = _make_found_inquiry(laporan.id)

        laporan.add_inquiry(second)

        assert laporan.status == LaporanStatus.FOUND_CLAIM_PENDING
        assert second in laporan.inquiries

    def test_make_inquiry_active_sets_laporan_in_progress_temuan(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id)
        laporan.add_inquiry(inquiry)

        laporan.make_inquiry_active(inquiry)

        assert laporan.status == LaporanStatus.IN_PROGRESS
        assert inquiry.status == InquiryStatus.ACTIVE

    def test_make_inquiry_active_sets_laporan_in_progress_hilang(self) -> None:
        laporan = _active_hilang()
        inquiry = _make_found_inquiry(laporan.id)
        laporan.add_inquiry(inquiry)

        laporan.make_inquiry_active(inquiry)

        assert laporan.status == LaporanStatus.IN_PROGRESS
        assert inquiry.status == InquiryStatus.ACTIVE

    def test_reject_active_inquiry_reverts_to_active_when_no_proposed(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id)
        laporan.add_inquiry(inquiry)
        laporan.make_inquiry_active(inquiry)

        laporan.reject_inquiry(inquiry)

        assert laporan.status == LaporanStatus.ACTIVE
        assert inquiry.status == InquiryStatus.REJECTED

    def test_reject_active_inquiry_reverts_to_claim_pending_when_proposed_remains(
        self,
    ) -> None:
        laporan = _active_temuan()
        active_inquiry = _make_claim_inquiry(laporan.id)
        laporan.add_inquiry(active_inquiry)
        laporan.make_inquiry_active(active_inquiry)
        proposed = _make_claim_inquiry(laporan.id, InquiryStatus.PROPOSED)
        laporan.inquiries.append(proposed)

        laporan.reject_inquiry(active_inquiry)

        assert laporan.status == LaporanStatus.CLAIM_PENDING
        assert active_inquiry.status == InquiryStatus.REJECTED

    def test_reject_active_inquiry_reverts_to_found_claim_pending_when_proposed_remains(
        self,
    ) -> None:
        laporan = _active_hilang()
        active_inquiry = _make_found_inquiry(laporan.id)
        laporan.add_inquiry(active_inquiry)
        laporan.make_inquiry_active(active_inquiry)
        proposed = _make_found_inquiry(laporan.id, InquiryStatus.PROPOSED)
        laporan.inquiries.append(proposed)

        laporan.reject_inquiry(active_inquiry)

        assert laporan.status == LaporanStatus.FOUND_CLAIM_PENDING
        assert active_inquiry.status == InquiryStatus.REJECTED

    def test_reject_last_proposed_reverts_laporan_to_active(self) -> None:
        laporan = _active_temuan()
        inquiry = _make_claim_inquiry(laporan.id)
        laporan.add_inquiry(inquiry)

        laporan.reject_inquiry(inquiry)

        assert laporan.status == LaporanStatus.ACTIVE
        assert inquiry.status == InquiryStatus.REJECTED

    def test_reject_proposed_keeps_claim_pending_when_other_proposed_remains(
        self,
    ) -> None:
        laporan = _active_temuan()
        first = _make_claim_inquiry(laporan.id)
        second = _make_claim_inquiry(laporan.id)
        laporan.add_inquiry(first)
        laporan.add_inquiry(second)

        laporan.reject_inquiry(first)

        assert laporan.status == LaporanStatus.CLAIM_PENDING
        assert first.status == InquiryStatus.REJECTED
