"""Add import_audit_logs table for Phase 3 audit trail.

Revision ID: 042
Revises: 041
Create Date: 2026-04-10 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '042'
down_revision = '041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create import_audit_logs table."""

    # Create import_audit_action enum
    op.execute("""
        CREATE TYPE import_audit_action AS ENUM (
            'task_created',
            'task_started',
            'extraction_started',
            'extraction_complete',
            'validation_started',
            'validation_complete',
            'import_started',
            'import_complete',
            'quality_gates_passed',
            'quality_gates_failed',
            'manual_review_required',
            'task_completed',
            'task_failed',
            'task_cancelled',
            'task_retried',
            'import_rolled_back'
        )
    """)

    # Create import_audit_logs table
    op.create_table(
        'import_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('import_task_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('action', sa.Enum(
            'task_created', 'task_started', 'extraction_started', 'extraction_complete',
            'validation_started', 'validation_complete', 'import_started', 'import_complete',
            'quality_gates_passed', 'quality_gates_failed', 'manual_review_required',
            'task_completed', 'task_failed', 'task_cancelled', 'task_retried',
            'import_rolled_back', name='import_audit_action', create_type=False
        ), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('exam_code', sa.String(50), nullable=False),
        sa.Column('category_code', sa.String(100), nullable=False),
        sa.Column('subject_code', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('questions_processed', sa.Integer(), nullable=True),
        sa.Column('questions_valid', sa.Integer(), nullable=True),
        sa.Column('questions_imported', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['import_task_id'], ['import_tasks.id'], name='fk_import_audit_logs_task_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_import_audit_logs_user_id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_import_audit_logs_tenant_id'),
    )

    # Create indices for common queries
    op.create_index('ix_import_audit_logs_user_id_created', 'import_audit_logs', ['user_id', 'created_at'], postgresql_using='brin')
    op.create_index('ix_import_audit_logs_task_created', 'import_audit_logs', ['import_task_id', 'created_at'], postgresql_using='brin')
    op.create_index('ix_import_audit_logs_action_status', 'import_audit_logs', ['action', 'status'])


def downgrade() -> None:
    """Drop import_audit_logs table."""

    # Drop indices
    op.drop_index('ix_import_audit_logs_action_status', table_name='import_audit_logs')
    op.drop_index('ix_import_audit_logs_task_created', table_name='import_audit_logs')
    op.drop_index('ix_import_audit_logs_user_id_created', table_name='import_audit_logs')

    # Drop table
    op.drop_table('import_audit_logs')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS import_audit_action')
