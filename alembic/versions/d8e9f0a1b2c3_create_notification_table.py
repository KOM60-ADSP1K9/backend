"""create notification table

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, Sequence[str], None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notification",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("recipient_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "inquiry_received",
                "inquiry_submitted",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.String(), nullable=False),
        sa.Column(
            "is_read",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("laporan_id", sa.UUID(), nullable=True),
        sa.Column("inquiry_id", sa.UUID(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["recipient_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["laporan_id"], ["laporan.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inquiry_id"], ["inquiry.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_recipient_user_id",
        "notification",
        ["recipient_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notification_laporan_id", "notification", ["laporan_id"], unique=False
    )
    op.create_index(
        "ix_notification_inquiry_id", "notification", ["inquiry_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_notification_inquiry_id", table_name="notification")
    op.drop_index("ix_notification_laporan_id", table_name="notification")
    op.drop_index("ix_notification_recipient_user_id", table_name="notification")
    op.drop_table("notification")
    sa.Enum(name="notificationtype").drop(op.get_bind(), checkfirst=False)
