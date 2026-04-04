"""Institution DPA fields and surcharge tracking.

Revision ID: 029
Revises: 028
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = "029"
down_revision = "028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("institutions", sa.Column("dpa_signed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("institutions", sa.Column("dpa_signer_name", sa.String(100), nullable=True))
    op.add_column("institutions", sa.Column("edu_student_limit", sa.Integer(), server_default=sa.text("30"), nullable=False))
    op.add_column("institutions", sa.Column("surcharge_confirmed", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade() -> None:
    op.drop_column("institutions", "surcharge_confirmed")
    op.drop_column("institutions", "edu_student_limit")
    op.drop_column("institutions", "dpa_signer_name")
    op.drop_column("institutions", "dpa_signed_at")
