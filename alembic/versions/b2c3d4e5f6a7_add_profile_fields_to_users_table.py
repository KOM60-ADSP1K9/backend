"""add profile fields to users table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-03-12 00:01:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("nim", sa.String(), nullable=True))
    op.add_column("users", sa.Column("fakultas", sa.String(), nullable=True))
    op.add_column("users", sa.Column("departemen", sa.String(), nullable=True))
    op.add_column("users", sa.Column("nip", sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "nip")
    op.drop_column("users", "departemen")
    op.drop_column("users", "fakultas")
    op.drop_column("users", "nim")
