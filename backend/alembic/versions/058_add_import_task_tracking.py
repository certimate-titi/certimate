"""Add import_tasks table for Phase 3 async processing.

Revision ID: 041
Revises: 040
Create Date: 2026-04-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '058'
down_revision = '057'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create import_tasks table and apscheduler_jobs table."""

    # Fully reset prior partial state so the migration is idempotent
    op.execute("DROP TABLE IF EXISTS import_tasks CASCADE")
    op.execute("DROP TYPE IF EXISTS import_task_status CASCADE")

    # Recreate enum (op.create_table below uses create_type=False to avoid double-create)
    op.execute("""
        CREATE TYPE import_task_status AS ENUM (
            'pending', 'processing', 'validating', 'importing',
            'completed', 'failed', 'cancelled'
        )
    """)
    op.create_table(
        'import_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('exam_code', sa.String(50), nullable=False),
        sa.Column('category_code', sa.String(100), nullable=False),
        sa.Column('subject_code', sa.String(100), nullable=False),
        sa.Column('exam_name', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('pending', 'processing', 'validating', 'importing', 'completed', 'failed', 'cancelled', name='import_task_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('total_questions', sa.Integer(), nullable=True),
        sa.Column('questions_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('questions_valid', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('questions_invalid', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('questions_imported', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('progress_percent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('validation_errors', sa.Text(), nullable=True),
        sa.Column('import_errors', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('historical_exam_id', postgresql.UUID(as_uuid=True), nullable=True, comment='FK to historical_exams after successful import'),
        sa.Column('question_pdf_path', sa.String(500), nullable=True),
        sa.Column('answer_pdf_path', sa.String(500), nullable=True),
        sa.Column('pdf_file_size', sa.Integer(), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quality_gates_passed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_manual_review', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_import_tasks_user_id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_import_tasks_tenant_id'),
        sa.ForeignKeyConstraint(['historical_exam_id'], ['historical_exams.id'], name='fk_import_tasks_historical_exam_id'),
    )

    # Create indices for common queries
    op.create_index('ix_import_tasks_user_id_status', 'import_tasks', ['user_id', 'status'])
    op.create_index('ix_import_tasks_status', 'import_tasks', ['status'])
    op.create_index('ix_import_tasks_created_at', 'import_tasks', ['created_at'], postgresql_using='brin')

    # Create apscheduler_jobs table for job persistence (idempotent)
    op.execute("DROP TABLE IF EXISTS apscheduler_jobs CASCADE")
    op.create_table(
        'apscheduler_jobs',
        sa.Column('id', sa.String(191), nullable=False),
        sa.Column('next_run_time', sa.Float(), nullable=True),
        sa.Column('job_state', sa.LargeBinary(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Drop import_tasks and apscheduler_jobs tables."""

    # Drop indices
    op.drop_index('ix_import_tasks_created_at', table_name='import_tasks')
    op.drop_index('ix_import_tasks_status', table_name='import_tasks')
    op.drop_index('ix_import_tasks_user_id_status', table_name='import_tasks')

    # Drop tables
    op.drop_table('apscheduler_jobs')
    op.drop_table('import_tasks')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS import_task_status')
