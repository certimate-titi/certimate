"""Add new resource types: docx, pptx, xlsx, doc, ppt, xls, audio, video.

Revision ID: 045
Revises: 044
Create Date: 2026-04-11

Extends the resource_type PostgreSQL enum with 8 new file types
to support Office documents, audio, and video uploads.
"""

revision = "045"
down_revision = "044"

from alembic import op


def upgrade():
    for val in ["docx", "pptx", "xlsx", "doc", "ppt", "xls", "audio", "video"]:
        op.execute(f"ALTER TYPE resource_type ADD VALUE IF NOT EXISTS '{val}'")


def downgrade():
    pass  # PostgreSQL enum values cannot be removed
