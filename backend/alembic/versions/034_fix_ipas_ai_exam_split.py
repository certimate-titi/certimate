"""Fix iPAS AI exam split — ensure 初級/中級 exams are correctly assigned.

Revision ID: 034
Revises: 033

Migration 026 tried to split AI 應用規劃師 exams by historical_source patterns,
but the split may not have worked on the cloud DB. This migration:
1. Reassigns exams with mid-level sources to AI 中級
2. Ensures 初級 only has fundamentals + application sources
3. Recalculates available_questions for all affected subjects
4. Clears stale resources/knowledge nodes so they regenerate correctly
"""
from alembic import op
import sqlalchemy as sa

revision = "034"
down_revision = "033"
branch_labels = None
depends_on = None

AI_OLD_ID = "b0000003-0001-0000-0000-000000000001"
AI_BEGINNER_ID = "b0000003-0001-0001-0000-000000000001"
AI_INTERMEDIATE_ID = "b0000003-0001-0002-0000-000000000001"


def upgrade():
    conn = op.get_bind()

    # Ensure 中級 subject exists
    conn.execute(sa.text("""
        INSERT INTO subjects (id, category_id, name, name_en, description, is_popular)
        VALUES (:id, :cat_id, :name, :name_en, :desc, true)
        ON CONFLICT (id) DO NOTHING
    """), {
        "id": AI_INTERMEDIATE_ID,
        "cat_id": "a0000001-0000-0000-0000-000000000004",
        "name": "AI 應用規劃師（中級）",
        "name_en": "AI Application Planner (Intermediate)",
        "desc": "經濟部產業發展署 iPAS — 人工智慧應用規劃師中級能力鑑定",
    })

    # Step 1: Move ALL AI planner exams to 初級 first (from old + any misassigned)
    conn.execute(sa.text("""
        UPDATE exams SET subject_id = :beginner
        WHERE subject_id IN (:old_id, :mid_id, :beg_id)
    """), {"beginner": AI_BEGINNER_ID, "old_id": AI_OLD_ID,
           "mid_id": AI_INTERMEDIATE_ID, "beg_id": AI_BEGINNER_ID})

    # Step 2: Move mid-level exams to 中級 (match on historical_source of their questions)
    conn.execute(sa.text("""
        UPDATE exams SET subject_id = :mid_id
        WHERE subject_id = :beg_id
          AND id IN (
            SELECT DISTINCT q.exam_id FROM questions q
            WHERE q.historical_source LIKE '%mid%'
          )
    """), {"mid_id": AI_INTERMEDIATE_ID, "beg_id": AI_BEGINNER_ID})

    # Step 3: Recalculate available_questions for all three subjects
    for subj_id in [AI_OLD_ID, AI_BEGINNER_ID, AI_INTERMEDIATE_ID]:
        conn.execute(sa.text("""
            UPDATE subjects SET available_questions = COALESCE((
                SELECT COUNT(*) FROM questions q
                JOIN exams e ON e.id = q.exam_id
                WHERE e.subject_id = :sid
                  AND q.historical_source IS NOT NULL
                  AND q.historical_source != ''
            ), 0)
            WHERE id = :sid
        """), {"sid": subj_id})

    # Step 4: Clear stale resources + knowledge nodes for 初級 so they regenerate
    # (The knowledge_nav_service will auto-recreate them with correct data)
    system_user_id = "00000000-0000-0000-0000-000000000001"

    # Nullify question FK references to knowledge_nodes that will be deleted
    for sid in [AI_BEGINNER_ID, AI_INTERMEDIATE_ID]:
        conn.execute(sa.text("""
            UPDATE questions SET node_id = NULL
            WHERE node_id IN (
                SELECT kn.id FROM knowledge_nodes kn
                WHERE kn.resource_id IN (
                    SELECT id FROM resources
                    WHERE subject_id = :sid AND user_id = :uid
                )
            )
        """), {"sid": sid, "uid": system_user_id})

    # Delete knowledge nodes first (FK to resources)
    conn.execute(sa.text("""
        DELETE FROM knowledge_nodes WHERE resource_id IN (
            SELECT id FROM resources
            WHERE subject_id = :sid AND user_id = :uid
        )
    """), {"sid": AI_BEGINNER_ID, "uid": system_user_id})

    # Delete the system resource
    conn.execute(sa.text("""
        DELETE FROM resources
        WHERE subject_id = :sid AND user_id = :uid
    """), {"sid": AI_BEGINNER_ID, "uid": system_user_id})

    # Also clear for 中級
    conn.execute(sa.text("""
        DELETE FROM knowledge_nodes WHERE resource_id IN (
            SELECT id FROM resources
            WHERE subject_id = :sid AND user_id = :uid
        )
    """), {"sid": AI_INTERMEDIATE_ID, "uid": system_user_id})

    conn.execute(sa.text("""
        DELETE FROM resources
        WHERE subject_id = :sid AND user_id = :uid
    """), {"sid": AI_INTERMEDIATE_ID, "uid": system_user_id})


def downgrade():
    conn = op.get_bind()
    # Move all back to old subject
    conn.execute(sa.text("""
        UPDATE exams SET subject_id = :old_id
        WHERE subject_id IN (:beg_id, :mid_id)
    """), {"old_id": AI_OLD_ID, "beg_id": AI_BEGINNER_ID, "mid_id": AI_INTERMEDIATE_ID})
