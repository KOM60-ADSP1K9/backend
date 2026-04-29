"""Repository tests for laporan persistence."""

from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.laporan import (
    LaporanHilang,
    LaporanStatus,
    LaporanTemuan,
    LaporanType,
)
from src.infrastructure.repositories.laporan_repository import LaporanRepository
from src.infrastructure.tables.lokasi_table import LokasiTable


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "factory",
        "expected_cls",
        "expected_type",
        "location_field",
        "date_field",
        "date_value",
    ),
    [
        (
            lambda location_id: LaporanHilang.New(
                photo="hilang.jpg",
                lost_at_location_id=location_id,
                lost_at_date=date(2026, 4, 1),
            ),
            LaporanHilang,
            LaporanType.HILANG,
            "lost_at_location_id",
            "lost_at_date",
            date(2026, 4, 1),
        ),
        (
            lambda location_id: LaporanTemuan.New(
                photo="temuan.jpg",
                found_at_location_id=location_id,
                found_at_date=date(2026, 4, 2),
            ),
            LaporanTemuan,
            LaporanType.TEMUAN,
            "found_at_location_id",
            "found_at_date",
            date(2026, 4, 2),
        ),
    ],
)
async def test_laporan_repository_round_trip(
    db_session: AsyncSession,
    factory,
    expected_cls,
    expected_type,
    location_field,
    date_field,
    date_value,
):
    """Saved laporan rows should round-trip as the correct concrete type."""
    other_location_field = (
        "found_at_location_id"
        if location_field == "lost_at_location_id"
        else "lost_at_location_id"
    )
    other_date_field = (
        "found_at_date" if date_field == "lost_at_date" else "lost_at_date"
    )
    alias_field = (
        "lostAtLocation"
        if location_field == "lost_at_location_id"
        else "foundAtLocation"
    )

    lokasi = LokasiTable(name="Lokasi A", latitude=-6.554321, longitude=106.723456)
    db_session.add(lokasi)
    await db_session.flush()

    repository = LaporanRepository(db_session)
    laporan = factory(lokasi.id)

    saved = await repository.save(laporan)

    assert isinstance(saved, expected_cls)
    assert saved.type is expected_type
    assert getattr(saved, location_field) == lokasi.id
    assert getattr(saved, date_field) == date_value
    assert getattr(saved, alias_field) == lokasi.id
    assert not hasattr(saved, other_location_field)
    assert not hasattr(saved, other_date_field)

    saved.status = LaporanStatus.ACTIVE
    updated = await repository.update(saved)

    assert isinstance(updated, expected_cls)
    assert updated.status is LaporanStatus.ACTIVE
    assert getattr(updated, location_field) == lokasi.id
    assert getattr(updated, date_field) == date_value
    assert getattr(updated, alias_field) == lokasi.id
    assert not hasattr(updated, other_location_field)
    assert not hasattr(updated, other_date_field)

    found = await repository.findById(updated.id)

    assert found is not None
    assert isinstance(found, expected_cls)
    assert found.id == updated.id
    assert found.type is expected_type
    assert found.status is LaporanStatus.ACTIVE
    assert getattr(found, location_field) == lokasi.id
    assert getattr(found, date_field) == date_value
    assert getattr(found, alias_field) == lokasi.id
    assert not hasattr(found, other_location_field)
    assert not hasattr(found, other_date_field)
