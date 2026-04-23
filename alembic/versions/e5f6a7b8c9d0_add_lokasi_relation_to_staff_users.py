"""add lokasi relationship to users

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-23 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("lokasi_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_users_lokasi_id_lokasi",
        "users",
        "lokasi",
        ["lokasi_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_users_lokasi_id", "users", ["lokasi_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_users_lokasi_id", table_name="users")
    op.drop_constraint("fk_users_lokasi_id_lokasi", "users", type_="foreignkey")
    op.drop_column("users", "lokasi_id")
