"""create inquiry table

Revision ID: a7b8c9d0e1f2
Revises: e6f7a8b9c0d2
Create Date: 2026-05-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "e6f7a8b9c0d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "inquiry",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "type",
            sa.Enum("claim", "found", name="inquirytype"),
            nullable=False,
        ),
        sa.Column("laporan_id", sa.UUID(), nullable=False),
        sa.Column("sender_user_id", sa.UUID(), nullable=False),
        sa.Column("message_content", sa.String(), nullable=False),
        sa.Column("send_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("claimer_contact", sa.String(), nullable=True),
        sa.Column("proof_of_ownership", sa.String(), nullable=True),
        sa.Column("ktm", sa.String(), nullable=True),
        sa.Column("finder_contact", sa.String(), nullable=True),
        sa.Column("photo", sa.String(), nullable=True),
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
        sa.CheckConstraint(
            "(type != 'claim' OR (claimer_contact IS NOT NULL "
            "AND proof_of_ownership IS NOT NULL AND ktm IS NOT NULL)) "
            "AND (type != 'claim' OR (finder_contact IS NULL AND photo IS NULL)) "
            "AND (type != 'found' OR (finder_contact IS NOT NULL AND photo IS NOT NULL)) "
            "AND (type != 'found' OR (claimer_contact IS NULL "
            "AND proof_of_ownership IS NULL AND ktm IS NULL))",
            name="ck_inquiry_type_fields",
        ),
        sa.ForeignKeyConstraint(["laporan_id"], ["laporan.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inquiry_laporan_id", "inquiry", ["laporan_id"], unique=False)
    op.create_index(
        "ix_inquiry_sender_user_id", "inquiry", ["sender_user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_inquiry_sender_user_id", table_name="inquiry")
    op.drop_index("ix_inquiry_laporan_id", table_name="inquiry")
    op.drop_table("inquiry")
    sa.Enum(name="inquirytype").drop(op.get_bind(), checkfirst=False)
