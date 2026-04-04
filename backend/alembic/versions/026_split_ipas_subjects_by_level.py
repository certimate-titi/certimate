"""Split iPAS subjects by level (初級/中級) and add available_questions to subjects.

Revision ID: 026
Revises: 025

AI 應用規劃師 → AI 應用規劃師（初級）+ AI 應用規劃師（中級）
巨量資料分析師 → 巨量資料分析師（初級）
資訊安全工程師 → 資訊安全工程師（初級）
"""
from alembic import op
import sqlalchemy as sa

revision = "026"
down_revision = "025"
branch_labels = None
depends_on = None

# New subject UUIDs for split levels
NEW_SUBJECTS = [
    # AI 應用規劃師 — split into 初級 + 中級
    ("b0000003-0001-0001-0000-000000000001", "a0000001-0000-0000-0000-000000000003",
     "AI 應用規劃師（初級）", "AI Application Planner (Beginner)",
     "經濟部產業發展署 iPAS — 人工智慧應用規劃師初級能力鑑定", True),
    ("b0000003-0001-0002-0000-000000000001", "a0000001-0000-0000-0000-000000000003",
     "AI 應用規劃師（中級）", "AI Application Planner (Intermediate)",
     "經濟部產業發展署 iPAS — 人工智慧應用規劃師中級能力鑑定", True),
    # 巨量資料分析師 — rename to 初級
    # (keep existing UUID, just rename)
    # 資訊安全工程師 — rename to 初級
    # (keep existing UUID, just rename)
]

# Mapping: question historical_source patterns -> new subject_id
# AI 初級: fundamentals, application
# AI 中級: mid_bigdata, mid_ml, mid_tech_planning
AI_BEGINNER_ID = "b0000003-0001-0001-0000-000000000001"
AI_INTERMEDIATE_ID = "b0000003-0001-0002-0000-000000000001"
AI_OLD_ID = "b0000003-0001-0000-0000-000000000001"


def upgrade():
    conn = op.get_bind()

    # 1. Add available_questions column to subjects
    op.add_column("subjects", sa.Column("available_questions", sa.Integer(), server_default="0"))

    # 2. Insert new AI 初級 and 中級 subjects
    for subj_id, cat_id, name, name_en, desc, is_pop in NEW_SUBJECTS:
        conn.execute(
            sa.text(
                "INSERT INTO subjects (id, category_id, name, name_en, description, is_popular) "
                "VALUES (:id, :cat_id, :name, :name_en, :desc, :is_pop) "
                "ON CONFLICT (id) DO NOTHING"
            ),
            {"id": subj_id, "cat_id": cat_id, "name": name, "name_en": name_en,
             "desc": desc, "is_pop": is_pop},
        )

    # 3. Re-assign exams from old AI subject to new ones
    # 初級: historical_source contains 'fundamentals' or 'application'
    conn.execute(sa.text("""
        UPDATE exams SET subject_id = :new_id
        WHERE subject_id = :old_id
          AND id IN (
            SELECT DISTINCT q.exam_id FROM questions q
            WHERE q.historical_source LIKE '%fundamentals%'
               OR q.historical_source LIKE '%application%'
          )
    """), {"new_id": AI_BEGINNER_ID, "old_id": AI_OLD_ID})

    # 中級: historical_source contains 'mid_'
    conn.execute(sa.text("""
        UPDATE exams SET subject_id = :new_id
        WHERE subject_id = :old_id
          AND id IN (
            SELECT DISTINCT q.exam_id FROM questions q
            WHERE q.historical_source LIKE '%ai mid%'
          )
    """), {"new_id": AI_INTERMEDIATE_ID, "old_id": AI_OLD_ID})

    # 4. Rename existing subjects to include level
    conn.execute(sa.text("""
        UPDATE subjects SET name = '巨量資料分析師（初級）',
                            name_en = 'Big Data Analyst (Beginner)'
        WHERE id = 'b0000003-0002-0000-0000-000000000002'
    """))
    conn.execute(sa.text("""
        UPDATE subjects SET name = '資訊安全工程師（初級）',
                            name_en = 'Information Security Engineer (Beginner)'
        WHERE id = 'b0000003-0005-0000-0000-000000000005'
    """))

    # 5. Reassign resources from old AI subject to new ones (table may not exist yet)
    has_resources = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'resources')"
    )).scalar()
    if has_resources:
        conn.execute(sa.text("""
            UPDATE resources SET subject_id = :new_id
            WHERE subject_id = :old_id
              AND (name LIKE '%初級%' OR name LIKE '%fundamentals%' OR name LIKE '%application%'
                   OR name LIKE '%beginner%')
        """), {"new_id": AI_BEGINNER_ID, "old_id": AI_OLD_ID})

        conn.execute(sa.text("""
            UPDATE resources SET subject_id = :new_id
            WHERE subject_id = :old_id
        """), {"new_id": AI_INTERMEDIATE_ID, "old_id": AI_OLD_ID})

    # 6. Update available_questions count for all subjects
    conn.execute(sa.text("""
        UPDATE subjects s SET available_questions = (
            SELECT COUNT(*) FROM questions q
            JOIN exams e ON e.id = q.exam_id
            WHERE e.subject_id = s.id
        )
    """))

    # 7. Reassign user_subjects from old AI to new (default to 初級) — table may not exist yet
    has_user_subjects = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_subjects')"
    )).scalar()
    if has_user_subjects:
        conn.execute(sa.text("""
            UPDATE user_subjects SET subject_id = :new_id
            WHERE subject_id = :old_id
        """), {"new_id": AI_BEGINNER_ID, "old_id": AI_OLD_ID})

    # 8. Reassign learning_journeys from old AI to new — table may not exist yet
    has_learning_journeys = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_journeys')"
    )).scalar()
    if has_learning_journeys:
        conn.execute(sa.text("""
            UPDATE learning_journeys SET subject_id = :new_id
            WHERE subject_id = :old_id
        """), {"new_id": AI_BEGINNER_ID, "old_id": AI_OLD_ID})


def downgrade():
    conn = op.get_bind()

    # Reassign back to old AI subject
    conn.execute(sa.text("""
        UPDATE exams SET subject_id = :old_id
        WHERE subject_id = :beg_id OR subject_id = :mid_id
    """), {"old_id": AI_OLD_ID, "beg_id": AI_BEGINNER_ID, "mid_id": AI_INTERMEDIATE_ID})

    has_resources = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'resources')"
    )).scalar()
    if has_resources:
        conn.execute(sa.text("""
            UPDATE resources SET subject_id = :old_id
            WHERE subject_id = :beg_id OR subject_id = :mid_id
        """), {"old_id": AI_OLD_ID, "beg_id": AI_BEGINNER_ID, "mid_id": AI_INTERMEDIATE_ID})

    has_user_subjects = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_subjects')"
    )).scalar()
    if has_user_subjects:
        conn.execute(sa.text("""
            UPDATE user_subjects SET subject_id = :old_id
            WHERE subject_id = :beg_id OR subject_id = :mid_id
        """), {"old_id": AI_OLD_ID, "beg_id": AI_BEGINNER_ID, "mid_id": AI_INTERMEDIATE_ID})

    has_learning_journeys = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_journeys')"
    )).scalar()
    if has_learning_journeys:
        conn.execute(sa.text("""
            UPDATE learning_journeys SET subject_id = :old_id
            WHERE subject_id = :beg_id OR subject_id = :mid_id
        """), {"old_id": AI_OLD_ID, "beg_id": AI_BEGINNER_ID, "mid_id": AI_INTERMEDIATE_ID})

    # Rename back
    conn.execute(sa.text("""
        UPDATE subjects SET name = '巨量資料分析師', name_en = 'Big Data Analyst'
        WHERE id = 'b0000003-0002-0000-0000-000000000002'
    """))
    conn.execute(sa.text("""
        UPDATE subjects SET name = '資訊安全工程師', name_en = 'Information Security Engineer'
        WHERE id = 'b0000003-0005-0000-0000-000000000005'
    """))

    # Delete new subjects
    conn.execute(sa.text("DELETE FROM subjects WHERE id = :id"), {"id": AI_BEGINNER_ID})
    conn.execute(sa.text("DELETE FROM subjects WHERE id = :id"), {"id": AI_INTERMEDIATE_ID})

    op.drop_column("subjects", "available_questions")
