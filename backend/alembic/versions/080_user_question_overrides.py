"""user_question_overrides — 使用者手動標記題目（已掌握 / 不再出現）。

Revision ID: 080
Revises: 079
"""

from alembic import op


revision = "080"
down_revision = "079"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_question_overrides (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            is_mastered BOOLEAN NOT NULL DEFAULT FALSE,
            marked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, question_id)
        );
        CREATE INDEX IF NOT EXISTS ix_uqo_user_mastered
            ON user_question_overrides (user_id, is_mastered);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_question_overrides CASCADE")
