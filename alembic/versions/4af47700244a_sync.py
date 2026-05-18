"""sync

No-op. Previously autogen wanted to drop inquiry indexes because the model
lacked index=True. Model updated to declare the indexes, matching the
original a7b8c9d0e1f2 migration.

Revision ID: 4af47700244a
Revises: a7b8c9d0e1f2
Create Date: 2026-05-12 23:33:24.199615

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "4af47700244a"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
