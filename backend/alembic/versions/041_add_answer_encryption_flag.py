"""041 - 欄位級加密：answers 表新增加密旗標欄位

Revision ID: 041
Revises: 040
Create Date: 2026-04-09

功能說明：
- 新增 answers.is_answer_encrypted (Boolean) — 記錄 selected_answer 是否已加密
- 新增 answers.encrypted_at (DateTime) — 記錄加密時間戳記（稽核用）
- 後續應用層 field_encryption.py 負責 Fernet 加解密；
  本 migration 僅補充 metadata 欄位，不修改 selected_answer 欄位類型
  （Fernet token 輸出仍為 String，相容現有結構）

金鑰輪替說明：
  使用 `enc:` 前綴區分明文與密文，應用層自動辨識。
  正式環境部署後請執行 scripts/encrypt_existing_answers.py 批次加密舊資料。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── answers 表：加密旗標與時間戳記 ──────────────────────────────────
    op.add_column(
        "answers",
        sa.Column(
            "is_answer_encrypted",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="selected_answer 是否已使用 Fernet 加密（應用層欄位級加密）",
        ),
    )
    op.add_column(
        "answers",
        sa.Column(
            "encrypted_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="欄位加密時間戳記（稽核用）",
        ),
    )

    # ── 建立索引（快速查詢尚未加密的舊資料，用於批次加密遷移）──────────
    op.create_index(
        "ix_answers_is_answer_encrypted",
        "answers",
        ["is_answer_encrypted"],
        postgresql_where=sa.text("is_answer_encrypted = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_answers_is_answer_encrypted", table_name="answers")
    op.drop_column("answers", "encrypted_at")
    op.drop_column("answers", "is_answer_encrypted")
