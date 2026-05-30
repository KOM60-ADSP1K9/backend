"""add inquiry status notification types

Adds the ``inquiry_accepted`` and ``inquiry_rejected`` values to the
``notificationtype`` enum so the inquiry sender can be notified when the laporan
owner activates or rejects their inquiry.

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-05-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'inquiry_accepted'")
    op.execute("ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS 'inquiry_rejected'")


def downgrade() -> None:
    """Downgrade schema.

    PostgreSQL cannot drop a value from an enum type. Removing these values would
    require recreating the type and rewriting every dependent column, which is
    unsafe if any row already uses them. Downgrade is intentionally a no-op.
    """
    pass
