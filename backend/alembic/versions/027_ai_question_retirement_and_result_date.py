"""AI question retirement fields + learning_journey result_date.

Revision ID: 027
Revises: 026
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa

revision = "027"
down_revision = "026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- questions: AI 考題退場欄位 ---
    op.add_column("questions", sa.Column("source_type", sa.String(20), server_default="historical"))
    op.add_column("questions", sa.Column("expires_at", sa.DateTime(timezone=True)))
    op.add_column("questions", sa.Column("retired_at", sa.DateTime(timezone=True)))
    op.add_column("questions", sa.Column("retention_reason", sa.String(50)))

    # 回填現有資料：有 historical_source → historical，無 → ai_generated
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE questions
        SET source_type = CASE
            WHEN historical_source IS NOT NULL THEN 'historical'
            ELSE 'ai_generated'
        END
    """))

    # --- learning_journeys: 放榜日期欄位 ---
    # 表可能不存在（尚未被其他 migration 建立）
    has_lj = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_journeys')"
    )).scalar()
    if has_lj:
        op.add_column("learning_journeys", sa.Column("result_date", sa.Date()))
        op.add_column("learning_journeys", sa.Column("exam_result_status", sa.String(20)))
        op.add_column("learning_journeys", sa.Column("data_expiry_date", sa.Date()))

    # 建立索引加速退場掃描
    op.create_index("ix_questions_source_type", "questions", ["source_type"])
    op.create_index(
        "ix_questions_retirement_scan",
        "questions",
        ["source_type", "retired_at", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_questions_retirement_scan", table_name="questions")
    op.drop_index("ix_questions_source_type", table_name="questions")

    conn = op.get_bind()
    has_lj = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_journeys')"
    )).scalar()
    if has_lj:
        op.drop_column("learning_journeys", "data_expiry_date")
        op.drop_column("learning_journeys", "exam_result_status")
        op.drop_column("learning_journeys", "result_date")

    op.drop_column("questions", "retention_reason")
    op.drop_column("questions", "retired_at")
    op.drop_column("questions", "expires_at")
    op.drop_column("questions", "source_type")
