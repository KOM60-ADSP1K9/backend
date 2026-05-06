"""add barang table and move photo from laporan

Revision ID: 7a8b9c0d1e2f
Revises: 6f7a8b9c0d1e
Create Date: 2026-05-06 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "7a8b9c0d1e2f"
down_revision: Union[str, Sequence[str], None] = "6f7a8b9c0d1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "barang",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("laporan_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("photo", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["laporan_id"], ["laporan.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("laporan_id", name="uq_barang_laporan_id"),
    )

    connection = op.get_bind()
    barang_table = sa.table(
        "barang",
        sa.column("id", sa.UUID()),
        sa.column("laporan_id", sa.UUID()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("photo", sa.String()),
    )
    existing_reports = connection.execute(
        sa.text("SELECT id, photo FROM laporan")
    ).mappings()
    barang_rows = [
        {
            "id": uuid4(),
            "laporan_id": row["id"],
            "name": "",
            "description": "",
            "photo": row["photo"],
        }
        for row in existing_reports
    ]
    if barang_rows:
        connection.execute(barang_table.insert(), barang_rows)

    op.drop_column("laporan", "photo")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("laporan", sa.Column("photo", sa.String(), nullable=True))

    connection = op.get_bind()
    existing_barang = connection.execute(
        sa.text("SELECT laporan_id, photo FROM barang")
    ).mappings()
    for row in existing_barang:
        connection.execute(
            sa.text("UPDATE laporan SET photo = :photo WHERE id = :id"),
            {"photo": row["photo"], "id": row["laporan_id"]},
        )

    op.drop_table("barang")
