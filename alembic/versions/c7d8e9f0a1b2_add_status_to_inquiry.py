"""add status to inquiry

Adds the `inquirystatus` enum type ('proposed', 'active', 'rejected') and a
non-null `status` column on the inquiry table defaulting to 'proposed'.

Revision ID: c7d8e9f0a1b2
Revises: 3d30b224c33b
Create Date: 2026-05-18 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "3d30b224c33b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


inquirystatus = postgresql.ENUM(
    "proposed",
    "active",
    "rejected",
    name="inquirystatus",
)


def upgrade() -> None:
    """Upgrade schema."""
    inquirystatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "inquiry",
        sa.Column(
            "status",
            inquirystatus,
            nullable=False,
            server_default="proposed",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("inquiry", "status")
    inquirystatus.drop(op.get_bind(), checkfirst=True)
