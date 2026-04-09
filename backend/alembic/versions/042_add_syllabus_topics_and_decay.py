"""Add syllabus_topics table and decay columns to node_mastery.

Revision ID: 041
Revises: 040
Create Date: 2026-04-09

動態知識庫 Phase 1：
- 新增 syllabus_topics 表（有機考綱樹）
- node_mastery 新增 SM-2 decay 欄位（base_mastery, ease_factor, timestamps, status）
- 資料回填：現有 mastery_rate → base_mastery
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. 建立 syllabus_topics 表 ──────────────────────────────────
    op.create_table(
        "syllabus_topics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("parent_id", UUID(as_uuid=True),
                  sa.ForeignKey("syllabus_topics.id"), nullable=True,
                  comment="父節點（NULL = 根節點）"),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weight", sa.Float(), server_default="1.0",
                  comment="聚合權重"),
        sa.Column("prerequisite_topic_id", UUID(as_uuid=True),
                  sa.ForeignKey("syllabus_topics.id"), nullable=True,
                  comment="前置知識溯源錨點"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"),
                  comment="軟刪除標記"),
        sa.Column("merged_into_id", UUID(as_uuid=True),
                  sa.ForeignKey("syllabus_topics.id"), nullable=True,
                  comment="合併繼承指標"),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True,
                  comment="多租戶隔離鍵"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_syllabus_topics_parent_id", "syllabus_topics", ["parent_id"])
    op.create_index("ix_syllabus_topics_tenant_id", "syllabus_topics", ["tenant_id"])
    op.create_index("ix_syllabus_topics_is_active", "syllabus_topics", ["is_active"])

    # ── 2. node_mastery 新增 SM-2 decay 欄位 ────────────────────────
    op.add_column("node_mastery", sa.Column(
        "base_mastery", sa.Float(), server_default="0.0",
        comment="基礎掌握度（0.0~1.0），僅由正式考試更新",
    ))
    op.add_column("node_mastery", sa.Column(
        "ease_factor", sa.Float(), server_default="2.5",
        comment="SM-2 ease factor（控制衰退速度）",
    ))
    op.add_column("node_mastery", sa.Column(
        "last_tested_at", sa.DateTime(timezone=True), nullable=True,
        comment="最後正式考試時間",
    ))
    op.add_column("node_mastery", sa.Column(
        "next_review_at", sa.DateTime(timezone=True), nullable=True,
        comment="下次建議複習時間",
    ))
    op.add_column("node_mastery", sa.Column(
        "status", sa.String(20), server_default="UNSEEN",
        comment="UNSEEN / CRITICAL / PENDING / MASTERED",
    ))

    # ── 3. 資料回填：mastery_rate → base_mastery ────────────────────
    op.execute(sa.text("""
        UPDATE node_mastery SET
            base_mastery = COALESCE(CAST(mastery_rate AS FLOAT), 0.0),
            last_tested_at = updated_at,
            next_review_at = updated_at + interval '14 days',
            status = CASE
                WHEN mastery_rate >= 0.7 THEN 'MASTERED'
                WHEN mastery_rate >= 0.4 THEN 'PENDING'
                WHEN mastery_rate > 0 THEN 'CRITICAL'
                ELSE 'UNSEEN'
            END
        WHERE base_mastery = 0.0 OR base_mastery IS NULL
    """))


def downgrade() -> None:
    op.drop_column("node_mastery", "status")
    op.drop_column("node_mastery", "next_review_at")
    op.drop_column("node_mastery", "last_tested_at")
    op.drop_column("node_mastery", "ease_factor")
    op.drop_column("node_mastery", "base_mastery")
    op.drop_index("ix_syllabus_topics_is_active", table_name="syllabus_topics")
    op.drop_index("ix_syllabus_topics_tenant_id", table_name="syllabus_topics")
    op.drop_index("ix_syllabus_topics_parent_id", table_name="syllabus_topics")
    op.drop_table("syllabus_topics")
