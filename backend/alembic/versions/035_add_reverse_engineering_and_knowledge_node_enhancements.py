"""Add reverse engineering tasks table, knowledge_node enhancements, and question suggested_node_id.

Revision ID: 035
Revises: 034

Feature 26: 考綱逆向工程
- New table: reverse_engineering_tasks
- New enum: reverse_engineering_status
- knowledge_nodes: add subject_id, exam_frequency, source_origin; make resource_id nullable
- questions: add suggested_node_id FK
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "035"
down_revision = "034"
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type (IF NOT EXISTS to handle partial runs)
    op.execute("DO $$ BEGIN CREATE TYPE reverse_engineering_status AS ENUM ('PROCESSING', 'COMPLETED', 'FAILED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # Create reverse_engineering_tasks table
    op.create_table(
        "reverse_engineering_tasks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("subject_id", UUID(as_uuid=True), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("triggered_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.VARCHAR(20), server_default="PROCESSING"),
        sa.Column("total_questions", sa.Integer, nullable=False),
        sa.Column("node_count", sa.Integer, nullable=True),
        sa.Column("coverage_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("max_depth", sa.Integer, nullable=True),
        sa.Column("orphan_node_count", sa.Integer, default=0, nullable=True),
        sa.Column("reliability", sa.String(10), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # knowledge_nodes: add subject_id column
    op.add_column("knowledge_nodes", sa.Column("subject_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_knowledge_nodes_subject_id",
        "knowledge_nodes", "subjects",
        ["subject_id"], ["id"],
    )

    # knowledge_nodes: add exam_frequency column
    op.add_column("knowledge_nodes", sa.Column("exam_frequency", sa.String(10), nullable=True))

    # knowledge_nodes: add source_origin column with default
    op.add_column("knowledge_nodes", sa.Column("source_origin", sa.String(20), server_default="document", nullable=False))

    # knowledge_nodes: make resource_id nullable (alter existing NOT NULL constraint)
    op.alter_column("knowledge_nodes", "resource_id", existing_type=UUID(as_uuid=True), nullable=True)

    # questions: add suggested_node_id column
    op.add_column("questions", sa.Column("suggested_node_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_questions_suggested_node_id",
        "questions", "knowledge_nodes",
        ["suggested_node_id"], ["id"],
    )


def downgrade():
    # questions: remove suggested_node_id
    op.drop_constraint("fk_questions_suggested_node_id", "questions", type_="foreignkey")
    op.drop_column("questions", "suggested_node_id")

    # knowledge_nodes: revert resource_id to NOT NULL
    op.alter_column("knowledge_nodes", "resource_id", existing_type=UUID(as_uuid=True), nullable=False)

    # knowledge_nodes: remove source_origin
    op.drop_column("knowledge_nodes", "source_origin")

    # knowledge_nodes: remove exam_frequency
    op.drop_column("knowledge_nodes", "exam_frequency")

    # knowledge_nodes: remove subject_id
    op.drop_constraint("fk_knowledge_nodes_subject_id", "knowledge_nodes", type_="foreignkey")
    op.drop_column("knowledge_nodes", "subject_id")

    # Drop reverse_engineering_tasks table
    op.drop_table("reverse_engineering_tasks")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS reverse_engineering_status")
