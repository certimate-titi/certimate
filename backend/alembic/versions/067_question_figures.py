"""Add figure_urls + figure_description to questions.

Revision ID: 067
Revises: 066

爬蟲抽出的圖像（PyMuPDF + Claude 配對）與圖描述須能存進 questions：
  - figure_urls       TEXT[]  圖片路徑/URL 陣列（順序依 PDF 內出現順序）
  - figure_description TEXT   Claude 對圖內容的文字描述（供無法顯示圖時 fallback）

Idempotent: IF NOT EXISTS。
"""

from alembic import op


revision = "067"
down_revision = "066"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE questions
            ADD COLUMN IF NOT EXISTS figure_urls TEXT[] NOT NULL DEFAULT '{}',
            ADD COLUMN IF NOT EXISTS figure_description TEXT
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE questions
            DROP COLUMN IF EXISTS figure_urls,
            DROP COLUMN IF EXISTS figure_description
    """)
