"""Cascade FK for subject and resource hard delete.

將 subjects / resources 的下游 FK 全部改為 ON DELETE CASCADE，
支援 P0 硬刪除功能。

改造範圍：
subjects 為 parent：
  - knowledge_nodes.subject_id  (原 fk_knowledge_nodes_subject_id，NO ACTION)
  - exams.subject_id            (自動命名，NO ACTION)
  - learning_journeys.subject_id (自動命名，NO ACTION)
  - resources.subject_id        (自動命名，NO ACTION)
  - reverse_engineering_tasks.subject_id (自動命名，NO ACTION)
  - merge_conflicts.subject_id  (自動命名，NO ACTION)
  - merge_histories.subject_id  (自動命名，NO ACTION)

resources 為 parent（已有 CASCADE，無需重建）：
  - resource_chunks.resource_id    → 已 CASCADE
  - resource_parse_jobs.resource_id → 已 CASCADE
  - resource_scaffolds.resource_id  → 已 CASCADE
  - question_candidates.resource_id → 已 CASCADE
  - user_hidden_resources.resource_id → 已 CASCADE
  - subject_default_resources.resource_id → 已 CASCADE

answers（已有 CASCADE，無需重建）：
  - answers.question_id → 已 CASCADE
  - answers.exam_id     → 已 CASCADE

Revision ID: 081
Revises: 080
"""

from alembic import op

revision = "081"
down_revision = "080"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── knowledge_nodes.subject_id ─────────────────────────────────────────
    # 原 migration 035 以具名 FK: fk_knowledge_nodes_subject_id
    op.execute(
        "ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS fk_knowledge_nodes_subject_id"
    )
    op.create_foreign_key(
        "fk_knowledge_nodes_subject_id",
        "knowledge_nodes",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── exams.subject_id ────────────────────────────────────────────────────
    op.execute(
        "ALTER TABLE exams DROP CONSTRAINT IF EXISTS exams_subject_id_fkey"
    )
    op.create_foreign_key(
        "exams_subject_id_fkey",
        "exams",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── learning_journeys.subject_id ────────────────────────────────────────
    op.execute(
        "ALTER TABLE learning_journeys DROP CONSTRAINT IF EXISTS learning_journeys_subject_id_fkey"
    )
    op.create_foreign_key(
        "learning_journeys_subject_id_fkey",
        "learning_journeys",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── resources.subject_id ────────────────────────────────────────────────
    op.execute(
        "ALTER TABLE resources DROP CONSTRAINT IF EXISTS resources_subject_id_fkey"
    )
    op.create_foreign_key(
        "resources_subject_id_fkey",
        "resources",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── reverse_engineering_tasks.subject_id ────────────────────────────────
    op.execute(
        "ALTER TABLE reverse_engineering_tasks DROP CONSTRAINT IF EXISTS reverse_engineering_tasks_subject_id_fkey"
    )
    op.create_foreign_key(
        "reverse_engineering_tasks_subject_id_fkey",
        "reverse_engineering_tasks",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── merge_conflicts.subject_id ──────────────────────────────────────────
    op.execute(
        "ALTER TABLE merge_conflicts DROP CONSTRAINT IF EXISTS merge_conflicts_subject_id_fkey"
    )
    op.create_foreign_key(
        "merge_conflicts_subject_id_fkey",
        "merge_conflicts",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── merge_histories.subject_id ──────────────────────────────────────────
    op.execute(
        "ALTER TABLE merge_histories DROP CONSTRAINT IF EXISTS merge_histories_subject_id_fkey"
    )
    op.create_foreign_key(
        "merge_histories_subject_id_fkey",
        "merge_histories",
        "subjects",
        ["subject_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 還原為 NO ACTION（不建議；恢復後硬刪除 subject 將再次 IntegrityError）

    # merge_histories.subject_id
    op.execute(
        "ALTER TABLE merge_histories DROP CONSTRAINT IF EXISTS merge_histories_subject_id_fkey"
    )
    op.create_foreign_key(
        "merge_histories_subject_id_fkey",
        "merge_histories",
        "subjects",
        ["subject_id"],
        ["id"],
    )

    # merge_conflicts.subject_id
    op.execute(
        "ALTER TABLE merge_conflicts DROP CONSTRAINT IF EXISTS merge_conflicts_subject_id_fkey"
    )
    op.create_foreign_key(
        "merge_conflicts_subject_id_fkey",
        "merge_conflicts",
        "subjects",
        ["subject_id"],
        ["id"],
    )

    # reverse_engineering_tasks.subject_id
    op.execute(
        "ALTER TABLE reverse_engineering_tasks DROP CONSTRAINT IF EXISTS reverse_engineering_tasks_subject_id_fkey"
    )
    op.create_foreign_key(
        "reverse_engineering_tasks_subject_id_fkey",
        "reverse_engineering_tasks",
        "subjects",
        ["subject_id"],
        ["id"],
    )

    # resources.subject_id
    op.execute(
        "ALTER TABLE resources DROP CONSTRAINT IF EXISTS resources_subject_id_fkey"
    )
    op.create_foreign_key(
        "resources_subject_id_fkey",
        "resources",
        "subjects",
        ["subject_id"],
        ["id"],
    )

    # learning_journeys.subject_id
    op.execute(
        "ALTER TABLE learning_journeys DROP CONSTRAINT IF EXISTS learning_journeys_subject_id_fkey"
    )
    op.create_foreign_key(
        "learning_journeys_subject_id_fkey",
        "learning_journeys",
        "subjects",
        ["subject_id"],
        ["id"],
    )

    # exams.subject_id
    op.execute(
        "ALTER TABLE exams DROP CONSTRAINT IF EXISTS exams_subject_id_fkey"
    )
    op.create_foreign_key(
        "exams_subject_id_fkey",
        "exams",
        "subjects",
        ["subject_id"],
        ["id"],
    )

    # knowledge_nodes.subject_id
    op.execute(
        "ALTER TABLE knowledge_nodes DROP CONSTRAINT IF EXISTS fk_knowledge_nodes_subject_id"
    )
    op.create_foreign_key(
        "fk_knowledge_nodes_subject_id",
        "knowledge_nodes",
        "subjects",
        ["subject_id"],
        ["id"],
    )
