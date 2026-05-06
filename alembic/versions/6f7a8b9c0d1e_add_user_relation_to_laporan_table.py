"""add user relation to laporan table

Revision ID: 6f7a8b9c0d1e
Revises: 4c261470d6c7
Create Date: 2026-05-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "6f7a8b9c0d1e"
down_revision: Union[str, Sequence[str], None] = "4c261470d6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("laporan", sa.Column("user_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_laporan_user_id_users",
        "laporan",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_laporan_user_id_users", "laporan", type_="foreignkey")
    op.drop_column("laporan", "user_id")
