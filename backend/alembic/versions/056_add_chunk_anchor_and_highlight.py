"""Add anchor_id and highlight fields to resource_chunks for physical-level navigation.

Revision ID: 056
Revises: 055
"""

from alembic import op
import sqlalchemy as sa

revision = "056"
down_revision = "055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "resource_chunks",
        sa.Column(
            "anchor_id",
            sa.String(255),
            nullable=True,
            comment="文件內錨點 ID（PDF: page_N, HTML: heading ID, YouTube: timestamp）",
        ),
    )
    op.add_column(
        "resource_chunks",
        sa.Column(
            "highlight_line_start",
            sa.Integer(),
            nullable=True,
            comment="原文高亮起始行（1-based）",
        ),
    )
    op.add_column(
        "resource_chunks",
        sa.Column(
            "highlight_line_end",
            sa.Integer(),
            nullable=True,
            comment="原文高亮結束行（1-based, inclusive）",
        ),
    )
    op.add_column(
        "resource_chunks",
        sa.Column(
            "highlight_char_start",
            sa.Integer(),
            nullable=True,
            comment="原文高亮起始字元偏移（0-based）",
        ),
    )
    op.add_column(
        "resource_chunks",
        sa.Column(
            "highlight_char_end",
            sa.Integer(),
            nullable=True,
            comment="原文高亮結束字元偏移（0-based, exclusive）",
        ),
    )


def downgrade() -> None:
    op.drop_column("resource_chunks", "highlight_char_end")
    op.drop_column("resource_chunks", "highlight_char_start")
    op.drop_column("resource_chunks", "highlight_line_end")
    op.drop_column("resource_chunks", "highlight_line_start")
    op.drop_column("resource_chunks", "anchor_id")
