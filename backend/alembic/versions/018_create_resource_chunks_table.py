"""Create resource_chunks table with pgvector support.

Revision ID: 018
Revises: 017
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("""
        CREATE TABLE resource_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            node_id UUID REFERENCES knowledge_nodes(id) ON DELETE SET NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            source_page_start INTEGER,
            source_page_end INTEGER,
            metadata_json JSON,
            embedding vector(1024),
            created_at TIMESTAMPTZ DEFAULT now()
        )
    """)

    op.execute(
        "CREATE INDEX idx_chunks_resource_id ON resource_chunks(resource_id)"
    )
    # IVFFlat index requires at least some rows to train on;
    # create it anyway — PG will use sequential scan until enough rows exist.
    op.execute(
        "CREATE INDEX idx_chunks_embedding ON resource_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("resource_chunks")
    op.execute("DROP EXTENSION IF EXISTS vector")
