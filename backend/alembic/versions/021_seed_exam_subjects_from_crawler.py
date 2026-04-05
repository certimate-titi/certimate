"""seed exam subjects from crawler catalog

Revision ID: 021
Revises: 020
Create Date: 2026-04-02

Seeds subject_categories and subjects based on the exam crawler catalog.
7 categories, 23 subjects from CertiMate historical exam database.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None

# Fixed UUIDs for cross-environment consistency
CATEGORY_IDS = {
    "金融": uuid.UUID("a0000001-0000-0000-0000-000000000001"),
    "IT": uuid.UUID("a0000001-0000-0000-0000-000000000004"),
    "語言": uuid.UUID("a0000001-0000-0000-0000-000000000005"),
    "醫療": uuid.UUID("a0000001-0000-0000-0000-000000000006"),
    "公務員": uuid.UUID("a0000001-0000-0000-0000-000000000007"),
}

SUBJECT_DATA = [
    # (uuid, category_key, name, name_en, description, is_popular)
    # available_questions 由 migration 026 從實際題庫計算，此處不預設
    # ── 金融 ──
    ("b0000001-0001-0000-0000-000000000001", "金融",
     "信託業業務人員", "Trust Business Personnel",
     "台灣金融研訓院 (TABF) — 信託業務專業測驗", True),
    ("b0000001-0002-0000-0000-000000000002", "金融",
     "證券商業務員", "Securities Salesperson",
     "證券暨期貨市場發展基金會 (SFI) — 證券交易相關法規與實務", True),
    ("b0000001-0003-0000-0000-000000000003", "金融",
     "人身保險業務員", "Life Insurance Agent",
     "台灣金融研訓院 (TABF) — 人身保險業務員資格測驗", True),
    ("b0000001-0004-0000-0000-000000000004", "金融",
     "期貨商業務員", "Futures Salesperson",
     "證券暨期貨市場發展基金會 (SFI) — 期貨交易法規與實務", True),
    ("b0000001-0005-0000-0000-000000000005", "金融",
     "防制洗錢與打擊資恐專業人員", "AML/CFT Professional",
     "證券暨期貨市場發展基金會 (SFI) — 防制洗錢與打擊資恐法令及實務", True),
    ("b0000001-0006-0000-0000-000000000006", "金融",
     "理財規劃人員", "Financial Planner",
     "台灣金融研訓院 (TABF) — 理財規劃人員專業能力測驗", True),
    ("b0000002-0001-0000-0000-000000000001", "金融",
     "不動產經紀人", "Real Estate Broker",
     "考選部 — 不動產經紀人專技普考", True),
    ("b0000002-0002-0000-0000-000000000002", "金融",
     "地政士", "Land Agent",
     "考選部 — 地政士專技普考", True),
    ("b0000002-0003-0000-0000-000000000003", "金融",
     "不動產估價師", "Real Estate Appraiser",
     "考選部 — 不動產估價師專技高考", False),
    ("b0000001-0007-0000-0000-000000000007", "金融",
     "CFA Level 1", "CFA Level 1",
     "CFA Institute — Chartered Financial Analyst Level I", True),

    # ── IT（含 iPAS） ──
    ("b0000003-0001-0000-0000-000000000001", "IT",
     "AI 應用規劃師", "AI Application Planner",
     "經濟部產業發展署 iPAS — 人工智慧應用規劃師能力鑑定", True),
    ("b0000003-0002-0000-0000-000000000002", "IT",
     "巨量資料分析師", "Big Data Analyst",
     "經濟部產業發展署 iPAS — 巨量資料分析師能力鑑定", False),
    ("b0000003-0003-0000-0000-000000000003", "IT",
     "物聯網應用工程師", "IoT Application Engineer",
     "經濟部產業發展署 iPAS — 物聯網應用工程師能力鑑定", False),
    ("b0000003-0004-0000-0000-000000000004", "IT",
     "區塊鏈智能合約開發者", "Blockchain Smart Contract Developer",
     "經濟部產業發展署 iPAS — 區塊鏈智能合約開發者能力鑑定", False),
    ("b0000003-0005-0000-0000-000000000005", "IT",
     "資訊安全工程師", "Information Security Engineer",
     "經濟部產業發展署 iPAS — 資訊安全工程師能力鑑定", True),
    ("b0000004-0001-0000-0000-000000000001", "IT",
     "AWS SAA", "AWS Solutions Architect Associate",
     "AWS Certified Solutions Architect – Associate", True),
    ("b0000004-0002-0000-0000-000000000002", "IT",
     "AWS SAP", "AWS Solutions Architect Professional",
     "AWS Certified Solutions Architect – Professional", False),
    ("b0000004-0003-0000-0000-000000000003", "IT",
     "GCP ACE", "Google Associate Cloud Engineer",
     "Google Cloud Associate Cloud Engineer", True),
    ("b0000004-0004-0000-0000-000000000004", "IT",
     "Azure AZ-900", "Microsoft Azure Fundamentals",
     "Microsoft Azure Fundamentals", False),

    # ── 語言 ──
    ("b0000005-0001-0000-0000-000000000001", "語言",
     "TOEIC", "TOEIC",
     "ETS — 多益英語測驗", True),
    ("b0000005-0002-0000-0000-000000000002", "語言",
     "JLPT N1", "JLPT N1",
     "日本語能力試驗 N1", False),

    # ── 醫療 ──
    ("b0000006-0001-0000-0000-000000000001", "醫療",
     "護理師", "Registered Nurse",
     "考選部 — 護理師國家考試", True),

    # ── 公務員 ──
    ("b0000007-0001-0000-0000-000000000001", "公務員",
     "普考", "Civil Service General Exam",
     "考選部 — 公務人員普通考試", False),
]


def upgrade():
    # Ensure available_questions column exists on subjects table
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'subjects' AND column_name = 'available_questions'"
    ))
    if not result.fetchone():
        op.add_column('subjects', sa.Column('available_questions', sa.Integer, server_default='0'))

    # Insert categories (skip if already exists)
    for name, cat_id in CATEGORY_IDS.items():
        sort_order = list(CATEGORY_IDS.keys()).index(name)
        conn.execute(
            sa.text(
                "INSERT INTO subject_categories (id, name, sort_order) "
                "VALUES (:id, :name, :sort_order) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": str(cat_id), "name": name, "sort_order": sort_order},
        )

    # Insert subjects (skip if already exists)
    for subj_id, cat_key, name, name_en, description, is_popular in SUBJECT_DATA:
        cat_id = CATEGORY_IDS[cat_key]
        conn.execute(
            sa.text(
                "INSERT INTO subjects (id, category_id, name, name_en, description, is_popular) "
                "VALUES (:id, :category_id, :name, :name_en, :description, :is_popular) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {
                "id": subj_id,
                "category_id": str(cat_id),
                "name": name,
                "name_en": name_en,
                "description": description,
                "is_popular": is_popular,
            },
        )


def downgrade():
    conn = op.get_bind()

    # Remove subjects first (FK)
    for subj_id, *_ in SUBJECT_DATA:
        conn.execute(
            sa.text("DELETE FROM subjects WHERE id = :id"),
            {"id": subj_id},
        )

    # Remove categories
    for cat_id in CATEGORY_IDS.values():
        conn.execute(
            sa.text("DELETE FROM subject_categories WHERE id = :id"),
            {"id": str(cat_id)},
        )
