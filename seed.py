"""CLI seeder."""

import argparse
import asyncio
from collections.abc import Callable
from typing import Any

from src.core import db_seeder
from src.domain.entity.user import UserRole
from src.infrastructure.services.bcrypt_password_service import BcryptPasswordService
from src.infrastructure.tables import LokasiTable, UserTable

PASSWORD_HASHER = BcryptPasswordService()

LOKASI_SEED_DATA: list[dict[str, Any]] = [
    {
        "name": "FMIPA Kering IPB",
        "latitude": -6.55766998308493,
        "longitude": 106.73123692186275,
    },
    {
        "name": "Gedung CCR (Common Class Room)",
        "latitude": -6.556105560715166,
        "longitude": 106.73109118579328,
    },
    {
        "name": "Gymnasium",
        "latitude": -6.557179431578245,
        "longitude": 106.73288830951118,
    },
    {
        "name": "Auditorium FMIPA IPB",
        "latitude": -6.557262682078246,
        "longitude": 106.72515189963565,
    },
    {
        "name": "Masjid Al-Hurriyyah",
        "latitude": -6.555744697441244,
        "longitude": 106.725408045655,
    },
    {
        "name": "Perpustakaan IPB",
        "latitude": -6.558878546805951,
        "longitude": 106.7270456472907,
    },
]


def build_user_seed_data() -> list[dict[str, Any]]:
    """Build seed rows for users table."""
    return [
        {
            "email": "mahasiswa1@apps.ipb.ac.id",
            "hashed_password": PASSWORD_HASHER.hash("Password123!"),
            "role": UserRole.MAHASISWA,
            "nip": None,
            "nim": "G64190001",
            "fakultas": "SSMI",
            "departemen": "Ilmu Komputer",
        },
        {
            "email": "mahasiswa2@apps.ipb.ac.id",
            "hashed_password": PASSWORD_HASHER.hash("Password123!"),
            "role": UserRole.MAHASISWA,
            "nip": None,
            "nim": "G64190002",
            "fakultas": "FTT",
            "departemen": "Teknik Mesin",
        },
        {
            "email": "staff1@apps.ipb.ac.id",
            "hashed_password": PASSWORD_HASHER.hash("Password123!"),
            "role": UserRole.STAFF,
            "nip": "19801980198019801980",
            "nim": None,
            "fakultas": None,
            "departemen": None,
        },
    ]


SEED_PLAN: list[tuple[str, type[Any], Callable[[], list[dict[str, Any]]]]] = [
    ("users", UserTable, build_user_seed_data),
    ("lokasi", LokasiTable, lambda: LOKASI_SEED_DATA),
]


async def run(operation: str) -> None:
    """Execute selected seeding operation for all configured tables."""
    if operation == "seed":
        total_inserted = 0
        for table_name, table, rows_factory in SEED_PLAN:
            inserted = await db_seeder.seed(table, rows_factory())
            total_inserted += inserted
            print(f"Seeded {inserted} rows into '{table_name}'.")
        print(f"Seed completed: {total_inserted} rows inserted in total.")
        return

    if operation == "reseed":
        for table_name, table, _ in SEED_PLAN:
            await db_seeder.truncate(table.__tablename__)
            print(f"Truncated '{table_name}'.")

        total_inserted = 0
        for table_name, table, rows_factory in SEED_PLAN:
            inserted = await db_seeder.seed(table, rows_factory())
            total_inserted += inserted
            print(f"Reseeded {inserted} rows into '{table_name}'.")
        print(f"Reseed completed: {total_inserted} rows inserted in total.")
        return

    if operation == "truncate":
        for table_name, table, _ in SEED_PLAN:
            await db_seeder.truncate(table.__tablename__)
            print(f"Truncated '{table_name}'.")
        print("Truncate completed for all configured tables.")
        return

    raise ValueError(f"Unsupported operation: {operation}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed all configured tables")
    parser.add_argument(
        "operation",
        choices=["seed", "reseed", "truncate"],
        help="Seeding operation to run",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(args.operation))
