"""Scaffold P0 redesign — retrieval_prompt + template_code + interaction log table.

Sprint 1 T02 — 對應 docs/scaffold-redesign-plan.md P0：

resource_scaffolds 加：
  - retrieval_prompt: text  讀前主動回想觸發題（從 takeaway 反推，不洩漏答案）
  - template_code: varchar(32)  K-06-study / K-06-slides / K-06-video / ...

新表 scaffold_interaction_log：
  - 記錄使用者與鷹架互動：viewed / revealed / recall_self_rated（沒想到/想到一半/完全想到）
  - 給 SM-2 排程演算法用的原始事件流（P3 才會接 SM-2，P0 先收集資料）

回滾安全：純加欄位 / 純新增表，歷史資料保留 NULL 不影響。

Revision ID: 082
Revises: 081
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "082"
down_revision = "081"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) resource_scaffolds 加欄位
    op.add_column(
        "resource_scaffolds",
        sa.Column("retrieval_prompt", sa.Text(), nullable=True),
    )
    op.add_column(
        "resource_scaffolds",
        sa.Column("template_code", sa.String(length=32), nullable=True),
    )

    # 2) 新表 scaffold_interaction_log
    op.create_table(
        "scaffold_interaction_log",
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
        sa.Column("event", sa.String(length=32), nullable=False),
        sa.Column("recall_quality", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_scaffold_interaction_log_user_scaffold",
        "scaffold_interaction_log",
        ["user_id", "scaffold_id"],
    )
    op.create_index(
        "ix_scaffold_interaction_log_created_at",
        "scaffold_interaction_log",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_scaffold_interaction_log_created_at", table_name="scaffold_interaction_log")
    op.drop_index("ix_scaffold_interaction_log_user_scaffold", table_name="scaffold_interaction_log")
    op.drop_table("scaffold_interaction_log")
    op.drop_column("resource_scaffolds", "template_code")
    op.drop_column("resource_scaffolds", "retrieval_prompt")
