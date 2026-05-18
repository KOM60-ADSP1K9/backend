"""add_in_progress_to_laporan

Adds new LaporanStatus enum values: 'found claim pending', 'in progress'.

Alembic autogen does not detect added values on existing Postgres enum types,
so this migration issues explicit ALTER TYPE ... ADD VALUE statements.

Revision ID: 3d30b224c33b
Revises: 4af47700244a
Create Date: 2026-05-12 23:34:47.590913

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3d30b224c33b"
down_revision: Union[str, Sequence[str], None] = "4af47700244a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VALUES = ("found claim pending", "in progress")

OLD_VALUES = (
    "draft",
    "active",
    "claim pending",
    "resolved",
    "closed",
    "self-resolved",
)


def upgrade() -> None:
    """Upgrade schema."""
    for value in NEW_VALUES:
        op.execute(f"ALTER TYPE laporanstatus ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """Downgrade schema.

    Postgres has no DROP VALUE on an enum type. Recreate the type with the
    original value set and rebind the dependent column.
    """
    old_values_sql = ", ".join(f"'{v}'" for v in OLD_VALUES)

    op.execute("ALTER TYPE laporanstatus RENAME TO laporanstatus_old")
    op.execute(f"CREATE TYPE laporanstatus AS ENUM ({old_values_sql})")
    op.execute(
        "ALTER TABLE laporan "
        "ALTER COLUMN status DROP DEFAULT, "
        "ALTER COLUMN status TYPE laporanstatus "
        "USING status::text::laporanstatus, "
        "ALTER COLUMN status SET DEFAULT 'draft'"
    )
    op.execute("DROP TYPE laporanstatus_old")
