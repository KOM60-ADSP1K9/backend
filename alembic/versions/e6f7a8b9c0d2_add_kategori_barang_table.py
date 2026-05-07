"""add kategori barang table

Revision ID: e6f7a8b9c0d2
Revises: 7a8b9c0d1e2f
Create Date: 2026-05-07 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import UUID

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e6f7a8b9c0d2"
down_revision: Union[str, Sequence[str], None] = "7a8b9c0d1e2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


KATEGORI_BARANG_SEEDS = [
    {"id": UUID("00000000-0000-0000-0000-000000000201"), "name": "Elektronik"},
    {"id": UUID("00000000-0000-0000-0000-000000000202"), "name": "Dokumen"},
    {"id": UUID("00000000-0000-0000-0000-000000000203"), "name": "Pakaian"},
    {"id": UUID("00000000-0000-0000-0000-000000000204"), "name": "Aksesoris"},
    {"id": UUID("00000000-0000-0000-0000-000000000205"), "name": "Tas"},
    {"id": UUID("00000000-0000-0000-0000-000000000206"), "name": "Kunci"},
    {
        "id": UUID("00000000-0000-0000-0000-000000000207"),
        "name": "Alat Tulis",
    },
    {"id": UUID("00000000-0000-0000-0000-000000000208"), "name": "Lainnya"},
]


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "kategori_barang",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_kategori_barang_name"),
    )

    kategori_barang_table = sa.table(
        "kategori_barang",
        sa.column("id", sa.UUID()),
        sa.column("name", sa.String()),
    )
    op.bulk_insert(kategori_barang_table, KATEGORI_BARANG_SEEDS)

    op.add_column(
        "barang",
        sa.Column("kategori_barang_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_barang_kategori_barang_id_kategori_barang",
        "barang",
        "kategori_barang",
        ["kategori_barang_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_barang_kategori_barang_id_kategori_barang",
        "barang",
        type_="foreignkey",
    )
    op.drop_column("barang", "kategori_barang_id")
    op.drop_table("kategori_barang")
