"""019 add DELETED to resource_status enum

Revision ID: 019
Revises: 018
Create Date: 2026-04-01
"""

from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE resource_status ADD VALUE IF NOT EXISTS 'DELETED';")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an enum type.
    pass
