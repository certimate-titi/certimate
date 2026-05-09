"""094 orphan_coach_conversations — AI 蘇格拉底教練對話欄位.

#9 AI 教練回應 Orphan 節點（蘇格拉底對話）：
  - ai_chat_sessions 加欄位：
      mode VARCHAR(32)      — error_explanation | socratic_orphan
      node_id UUID          — FK → knowledge_nodes（socratic_orphan 時使用）
      score_concept FLOAT   — 概念接觸度（0 / 0.5 / 1，LLM 評分）
      score_reasoning FLOAT — 推理連結度（0 / 0.5 / 1，LLM 評分）
      score_initiative FLOAT— 主動性（0 / 0.5，規則判斷）
      final_score FLOAT     — 該輪總分（最高 2.5）
      mastery_committed BOOL— mastery 降權是否已寫入
      paused_at TIMESTAMPTZ — C.4.4 可續對話：3 分鐘無回應暫停時間

對應 docs/design/orphan-mitigation-design.md 區塊 C。
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "094"
down_revision = "093"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ai_chat_sessions 加 orphan coach 欄位 ──────────────────────
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "mode",
            sa.String(32),
            nullable=True,
            comment="對話模式：error_explanation | socratic_orphan（NULL = 舊資料相容）",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "node_id",
            UUID(as_uuid=True),
            sa.ForeignKey("knowledge_nodes.id", ondelete="CASCADE"),
            nullable=True,
            comment="socratic_orphan 模式：目標 orphan 知識節點",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "score_concept",
            sa.Float(),
            nullable=True,
            comment="最新輪概念接觸度評分（0 / 0.5 / 1）",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "score_reasoning",
            sa.Float(),
            nullable=True,
            comment="最新輪推理連結度評分（0 / 0.5 / 1）",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "score_initiative",
            sa.Float(),
            nullable=True,
            comment="最新輪主動性評分（0 / 0.5，規則判斷）",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "final_score",
            sa.Float(),
            nullable=True,
            comment="最新輪總分（最高 2.5）",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "mastery_committed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="是否已將蘇格拉底對話 mastery 降權寫入 node_mastery",
        ),
    )
    op.add_column(
        "ai_chat_sessions",
        sa.Column(
            "paused_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="C.4.4：3 分鐘無回應暫停時間，下次進入同節點自動接續",
        ),
    )

    # ── ai_chat_messages 加 socratic 評分欄位 ──────────────────────
    op.add_column(
        "ai_chat_messages",
        sa.Column(
            "score_concept",
            sa.Float(),
            nullable=True,
            comment="該輪學生回答之概念接觸度（0/0.5/1，僅 user role 有值）",
        ),
    )
    op.add_column(
        "ai_chat_messages",
        sa.Column(
            "score_reasoning",
            sa.Float(),
            nullable=True,
            comment="該輪學生回答之推理連結度（0/0.5/1，僅 user role 有值）",
        ),
    )
    op.add_column(
        "ai_chat_messages",
        sa.Column(
            "score_initiative",
            sa.Float(),
            nullable=True,
            comment="該輪學生主動性（0/0.5，規則判斷，僅 user role 有值）",
        ),
    )
    op.add_column(
        "ai_chat_messages",
        sa.Column(
            "round_score",
            sa.Float(),
            nullable=True,
            comment="該輪總分（最高 2.5，僅 user role 有值）",
        ),
    )

    # ── index for node_id + mode 查詢 ──────────────────────────────
    op.create_index(
        "ix_ai_chat_sessions_node_id",
        "ai_chat_sessions",
        ["node_id"],
    )
    op.create_index(
        "ix_ai_chat_sessions_mode",
        "ai_chat_sessions",
        ["mode"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_chat_sessions_mode", table_name="ai_chat_sessions")
    op.drop_index("ix_ai_chat_sessions_node_id", table_name="ai_chat_sessions")

    op.drop_column("ai_chat_messages", "round_score")
    op.drop_column("ai_chat_messages", "score_initiative")
    op.drop_column("ai_chat_messages", "score_reasoning")
    op.drop_column("ai_chat_messages", "score_concept")

    op.drop_column("ai_chat_sessions", "paused_at")
    op.drop_column("ai_chat_sessions", "mastery_committed")
    op.drop_column("ai_chat_sessions", "final_score")
    op.drop_column("ai_chat_sessions", "score_initiative")
    op.drop_column("ai_chat_sessions", "score_reasoning")
    op.drop_column("ai_chat_sessions", "score_concept")
    op.drop_column("ai_chat_sessions", "node_id")
    op.drop_column("ai_chat_sessions", "mode")
