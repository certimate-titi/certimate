"""Scaffold SM-2 review schedule table — Sprint 5 P4 (T44).

新表：scaffold_review_schedule
- 對每個 (user_id, scaffold_id) 維護 SM-2 演算法狀態
- 由 scaffold_interaction_log recall_self_rated 事件 → SM-2 算法 → 寫入此表
- 後端 /scaffold-reviews/due endpoint 取「今日該複習」清單

SM-2 演算法欄位（per Wikipedia / SuperMemo SM-2）：
- ease_factor: float（記憶因子，初始 2.5，範圍 1.3-3.0+）
- interval_days: int（下次複習間隔天數，初始 1）
- repetitions: int（連續答對次數，初始 0）
- next_review_at: timestamp（下次該複習時間）

Revision ID: 086
Revises: 085
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "086"
down_revision = "085"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scaffold_review_schedule",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "scaffold_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resource_scaffolds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ease_factor",
            sa.Float(),
            nullable=False,
            server_default=sa.text("2.5"),
            comment="SM-2 記憶因子，初始 2.5，範圍建議 1.3-3.0",
        ),
        sa.Column(
            "interval_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
            comment="下次複習間隔天數",
        ),
        sa.Column(
            "repetitions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment="連續答對次數",
        ),
        sa.Column(
            "next_review_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "scaffold_id", name="uq_scaffold_review_user_scaffold"
        ),
    )
    op.create_index(
        "ix_scaffold_review_user_due",
        "scaffold_review_schedule",
        ["user_id", "next_review_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_scaffold_review_user_due", table_name="scaffold_review_schedule"
    )
    op.drop_table("scaffold_review_schedule")
