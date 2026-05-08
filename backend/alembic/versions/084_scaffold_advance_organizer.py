"""Scaffold type add `advance_organizer` + `concept_extract` — Sprint 4 P3 (T33).

新增鷹架類別：
- advance_organizer：讀前定錨（Ausubel Subsumption Theory）
  → 章節閱讀**前**先看的引導問句，幫讀者先建立心智錨點
- concept_extract：考古題核心概念提煉（K-06-quiz 專用）
  → Sprint 2 P1 借用 takeaway type，Sprint 4 正式擴 enum

Revision ID: 084
Revises: 083
"""

from alembic import op

revision = "084"
down_revision = "083"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE resource_scaffold_type ADD VALUE IF NOT EXISTS 'advance_organizer'"
    )
    op.execute(
        "ALTER TYPE resource_scaffold_type ADD VALUE IF NOT EXISTS 'concept_extract'"
    )


def downgrade() -> None:
    # Postgres 不支援 DROP enum value（同 083 規則）
    pass
