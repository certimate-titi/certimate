"""093 orphan_scaffold_fill — AI 補洞鷹架（Orphan Auto-Fill Scaffold）.

#2 AI 自動補洞鷹架：
  1. resource_scaffolds 加欄位：trust_level / confidence_score /
     evidence_question_ids / is_orphan_fill / generation_failure_reason
  2. 新表 scaffold_review_queue：學生回報不準確的佇列（RLS 啟用）

對應 docs/design/orphan-mitigation-design.md 區塊 A。
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY


revision = "093"
down_revision = "092"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1a. resource_scaffolds.resource_id → nullable（orphan scaffold 無 resource）
    op.alter_column(
        "resource_scaffolds",
        "resource_id",
        nullable=True,
        existing_nullable=False,
        existing_type=sa.UUID(),
    )

    # ── 1b. resource_scaffolds 加欄位 ──────────────────────────────
    op.add_column(
        "resource_scaffolds",
        sa.Column(
            "trust_level",
            sa.String(32),
            nullable=True,
            comment="HUMAN_VERIFIED / SYSTEM_GENERATED / AI_INFERRED / PENDING_REVIEW",
        ),
    )
    op.add_column(
        "resource_scaffolds",
        sa.Column(
            "confidence_score",
            sa.Integer(),
            nullable=True,
            comment="AI 補洞鷹架信心分數 0-100；正式鷹架為 NULL",
        ),
    )
    op.add_column(
        "resource_scaffolds",
        sa.Column(
            "evidence_question_ids",
            ARRAY(UUID(as_uuid=True)),
            nullable=True,
            comment="佐證考古題 id 陣列（最多 8 題）",
        ),
    )
    op.add_column(
        "resource_scaffolds",
        sa.Column(
            "is_orphan_fill",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="是否為 AI 補洞鷹架（K-ORPHAN-01 生成）",
        ),
    )
    op.add_column(
        "resource_scaffolds",
        sa.Column(
            "generation_failure_reason",
            sa.String(64),
            nullable=True,
            comment="生成失敗原因：evidence_insufficient / semantic_drift / url_detected / llm_error",
        ),
    )

    # ── 2. scaffold_review_queue 新表 ─────────────────────────────
    op.create_table(
        "scaffold_review_queue",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "scaffold_id",
            UUID(as_uuid=True),
            sa.ForeignKey("resource_scaffolds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reporter_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reason_code",
            sa.String(32),
            nullable=False,
            comment="definition_wrong / example_wrong / answer_wrong / unrelated / other",
        ),
        sa.Column(
            "note",
            sa.String(100),
            nullable=True,
            comment="自由填寫說明（限 100 字）",
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="多租戶隔離鍵",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_scaffold_review_queue_scaffold_id",
        "scaffold_review_queue",
        ["scaffold_id"],
    )
    op.create_index(
        "ix_scaffold_review_queue_tenant",
        "scaffold_review_queue",
        ["tenant_id"],
    )

    # ── 3. RLS policy for scaffold_review_queue ───────────────────
    op.execute("ALTER TABLE scaffold_review_queue ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY scaffold_review_queue_tenant_isolation
        ON scaffold_review_queue
        USING (
            tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid
        )
    """)


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS scaffold_review_queue_tenant_isolation "
        "ON scaffold_review_queue"
    )
    op.drop_index("ix_scaffold_review_queue_scaffold_id",
                  table_name="scaffold_review_queue")
    op.drop_index("ix_scaffold_review_queue_tenant",
                  table_name="scaffold_review_queue")
    op.drop_table("scaffold_review_queue")

    op.drop_column("resource_scaffolds", "generation_failure_reason")
    op.drop_column("resource_scaffolds", "is_orphan_fill")
    op.drop_column("resource_scaffolds", "evidence_question_ids")
    op.drop_column("resource_scaffolds", "confidence_score")
    op.drop_column("resource_scaffolds", "trust_level")
    op.alter_column(
        "resource_scaffolds",
        "resource_id",
        nullable=False,
        existing_nullable=True,
        existing_type=sa.UUID(),
    )
