"""add bloom_category and historical_source to questions

Revision ID: 022
Revises: 021
Create Date: 2026-04-02

Adds bloom_category enum column and historical_source varchar to questions table,
matching DBML spec for exam trend analysis and historical exam tracking.
"""
from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade():
    # bloom_category enum should already exist from earlier migration;
    # create only if not present
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_type WHERE typname = 'bloom_category'"
    )).fetchone()
    if not result:
        op.execute("""
            CREATE TYPE bloom_category AS ENUM (
                'remember', 'understand', 'apply', 'analyze', 'evaluate', 'create'
            )
        """)

    op.add_column("questions", sa.Column(
        "bloom_category",
        sa.Enum("remember", "understand", "apply", "analyze", "evaluate", "create",
                name="bloom_category", create_type=False),
        nullable=True,
    ))
    op.add_column("questions", sa.Column(
        "historical_source",
        sa.String(255),
        nullable=True,
    ))


def downgrade():
    op.drop_column("questions", "historical_source")
    op.drop_column("questions", "bloom_category")
