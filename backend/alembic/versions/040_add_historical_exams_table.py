"""Add historical_exams table and link questions to it.

Revision ID: 040
Revises: 039
Create Date: 2026-04-08

新增歷史考試目錄表，支援爬蟲匯入的考古題：
- 建立 historical_exams 表（考試代碼/類科/科目唯一索引）
- questions.exam_id 改為 nullable（歷史題目不需要 user exam）
- questions 新增 historical_exam_id FK
- CHECK 約束確保每題至少屬於一個來源
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "040"
down_revision = "039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. 建立 historical_exams 表 ─────────────────────────────────────
    op.create_table(
        "historical_exams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("exam_code", sa.String(20), nullable=False,
                  comment="考選部考試代碼，如 114010"),
        sa.Column("category_code", sa.String(20), nullable=True,
                  comment="類科代碼，如 501"),
        sa.Column("subject_code", sa.String(20), nullable=True,
                  comment="科目代碼，如 0101"),
        sa.Column("exam_name", sa.String(255), nullable=True,
                  comment="考試名稱，如 114年初等考試"),
        sa.Column("category_name", sa.String(255), nullable=True,
                  comment="類科名稱，如 一般行政"),
        sa.Column("subject_name", sa.String(255), nullable=True,
                  comment="科目名稱，如 國文"),
        sa.Column("source", sa.String(255), nullable=True,
                  server_default="考選部考畢試題查詢平臺",
                  comment="資料來源"),
        sa.Column("total_questions", sa.Integer(), nullable=True,
                  comment="題目總數"),
        sa.Column("year", sa.Integer(), nullable=True,
                  comment="民國年"),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True,
                  comment="多租戶隔離鍵"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    # 唯一索引：(exam_code, category_code, subject_code)
    op.create_unique_constraint(
        "uq_historical_exam_identity",
        "historical_exams",
        ["exam_code", "category_code", "subject_code"],
    )
    op.create_index("ix_historical_exams_tenant_id", "historical_exams", ["tenant_id"])
    op.create_index("ix_historical_exams_exam_code", "historical_exams", ["exam_code"])
    op.create_index("ix_historical_exams_year", "historical_exams", ["year"])

    # ── 2. questions.exam_id 改為 nullable ──────────────────────────────
    op.alter_column(
        "questions", "exam_id",
        existing_type=UUID(as_uuid=True),
        nullable=True,
        comment="使用者考試 FK（AI 生成題 / 模擬考），歷史題可為 NULL",
    )

    # ── 3. questions 新增 historical_exam_id ─────────────────────────────
    op.add_column(
        "questions",
        sa.Column(
            "historical_exam_id",
            UUID(as_uuid=True),
            sa.ForeignKey("historical_exams.id", ondelete="CASCADE"),
            nullable=True,
            comment="歷史考試目錄 FK（爬蟲匯入的考古題）",
        ),
    )
    op.create_index(
        "ix_questions_historical_exam_id", "questions", ["historical_exam_id"]
    )

    # ── 4. CHECK 約束：每題至少屬於一方 ──────────────────────────────────
    op.create_check_constraint(
        "ck_questions_has_parent",
        "questions",
        "exam_id IS NOT NULL OR historical_exam_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_questions_has_parent", "questions", type_="check")
    op.drop_index("ix_questions_historical_exam_id", table_name="questions")
    op.drop_column("questions", "historical_exam_id")
    op.alter_column(
        "questions", "exam_id",
        existing_type=UUID(as_uuid=True),
        nullable=False,
    )
    op.drop_index("ix_historical_exams_year", table_name="historical_exams")
    op.drop_index("ix_historical_exams_exam_code", table_name="historical_exams")
    op.drop_index("ix_historical_exams_tenant_id", table_name="historical_exams")
    op.drop_constraint("uq_historical_exam_identity", "historical_exams", type_="unique")
    op.drop_table("historical_exams")
