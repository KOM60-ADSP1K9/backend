"""add role to users table

Revision ID: a1b2c3d4e5f6
Revises: 73c041bdb298
Create Date: 2026-03-12 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "73c041bdb298"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

userrole_enum = sa.Enum("MAHASISWA", "STAFF", name="userrole")


def upgrade() -> None:
    """Upgrade schema."""
    userrole_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column(
            "role",
            userrole_enum,
            nullable=False,
            server_default="MAHASISWA",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
    userrole_enum.drop(op.get_bind(), checkfirst=True)
