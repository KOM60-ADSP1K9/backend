"""Unit tests for Laporan date validation (lost_at_date / found_at_date)."""

import datetime
from uuid import uuid4

import pytest

from src.domain.entity.laporan import LaporanHilang, LaporanStatus, LaporanTemuan


def _today() -> datetime.date:
    return datetime.datetime.now(datetime.timezone.utc).date()


def _yesterday() -> datetime.date:
    return _today() - datetime.timedelta(days=1)


def _tomorrow() -> datetime.date:
    return _today() + datetime.timedelta(days=1)


class TestLaporanHilangDateValidation:
    def test_new_accepts_past_lost_at_date(self) -> None:
        laporan = LaporanHilang.New(
            user_id=uuid4(),
            lost_at_date=_yesterday(),
        )

        assert laporan.lost_at_date == _yesterday()

    def test_new_accepts_today_lost_at_date(self) -> None:
        laporan = LaporanHilang.New(
            user_id=uuid4(),
            lost_at_date=_today(),
        )

        assert laporan.lost_at_date == _today()

    def test_new_accepts_none_lost_at_date(self) -> None:
        laporan = LaporanHilang.New(
            user_id=uuid4(),
            lost_at_date=None,
        )

        assert laporan.lost_at_date is None

    def test_new_rejects_future_lost_at_date(self) -> None:
        with pytest.raises(ValueError, match="lost_at_date cannot be in the future"):
            LaporanHilang.New(
                user_id=uuid4(),
                lost_at_date=_tomorrow(),
            )

    def test_update_accepts_past_lost_at_date(self) -> None:
        laporan = LaporanHilang.New(
            user_id=uuid4(),
            lost_at_date=_yesterday(),
            status=LaporanStatus.ACTIVE,
        )

        laporan.update(lost_at_location_id=uuid4(), lost_at_date=_yesterday())

        assert laporan.lost_at_date == _yesterday()

    def test_update_rejects_future_lost_at_date(self) -> None:
        laporan = LaporanHilang.New(
            user_id=uuid4(),
            lost_at_date=_yesterday(),
            status=LaporanStatus.ACTIVE,
        )

        with pytest.raises(ValueError, match="lost_at_date cannot be in the future"):
            laporan.update(lost_at_location_id=uuid4(), lost_at_date=_tomorrow())

        assert laporan.lost_at_date == _yesterday()


class TestLaporanTemuanDateValidation:
    def test_new_accepts_past_found_at_date(self) -> None:
        laporan = LaporanTemuan.New(
            user_id=uuid4(),
            found_at_date=_yesterday(),
        )

        assert laporan.found_at_date == _yesterday()

    def test_new_accepts_today_found_at_date(self) -> None:
        laporan = LaporanTemuan.New(
            user_id=uuid4(),
            found_at_date=_today(),
        )

        assert laporan.found_at_date == _today()

    def test_new_accepts_none_found_at_date(self) -> None:
        laporan = LaporanTemuan.New(
            user_id=uuid4(),
            found_at_date=None,
        )

        assert laporan.found_at_date is None

    def test_new_rejects_future_found_at_date(self) -> None:
        with pytest.raises(ValueError, match="found_at_date cannot be in the future"):
            LaporanTemuan.New(
                user_id=uuid4(),
                found_at_date=_tomorrow(),
            )

    def test_update_accepts_past_found_at_date(self) -> None:
        laporan = LaporanTemuan.New(
            user_id=uuid4(),
            found_at_date=_yesterday(),
            status=LaporanStatus.ACTIVE,
        )

        laporan.update(found_at_location_id=uuid4(), found_at_date=_yesterday())

        assert laporan.found_at_date == _yesterday()

    def test_update_rejects_future_found_at_date(self) -> None:
        laporan = LaporanTemuan.New(
            user_id=uuid4(),
            found_at_date=_yesterday(),
            status=LaporanStatus.ACTIVE,
        )

        with pytest.raises(ValueError, match="found_at_date cannot be in the future"):
            laporan.update(found_at_location_id=uuid4(), found_at_date=_tomorrow())

        assert laporan.found_at_date == _yesterday()
