"""add confidence column to answers

Revision ID: 023
Revises: 022
Create Date: 2026-04-03

Adds confidence level to answers table for confidence-based learning (CBL).
Supports four-quadrant analysis: confident+correct, confident+wrong (dangerous blindspot),
guessing+correct (lucky), guessing+wrong (expected weakness).
"""
from alembic import op
import sqlalchemy as sa

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade():
    # confidence: 'high' (很確定), 'medium' (有點把握), 'low' (完全猜測), NULL (未標記)
    op.add_column("answers", sa.Column(
        "confidence",
        sa.String(10),
        nullable=True,
    ))


def downgrade():
    op.drop_column("answers", "confidence")
