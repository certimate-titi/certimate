"""Create knowledge_nodes, node_mastery, ai_chat_sessions, ai_chat_messages, ai_cooldowns, plan_quotas tables.

Revision ID: 003
Revises: 002
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # knowledge_nodes
    op.create_table(
        'knowledge_nodes',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('resource_id', UUID(as_uuid=True), sa.ForeignKey('resources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('knowledge_nodes.id'), nullable=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('depth', sa.Integer, server_default='0'),
        sa.Column('sort_order', sa.Integer, server_default='0'),
        sa.Column('source_page_number', sa.Integer, nullable=True),
        sa.Column('source_timestamp_seconds', sa.Integer, nullable=True),
        sa.Column('source_text', sa.Text, nullable=True),
        sa.Column('available_questions', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # node_mastery
    op.create_table(
        'node_mastery',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_id', UUID(as_uuid=True), sa.ForeignKey('knowledge_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('correct_count', sa.Integer, server_default='0'),
        sa.Column('total_count', sa.Integer, server_default='0'),
        sa.Column('mastery_rate', sa.Numeric(5, 2), server_default='0'),
        sa.Column('color', sa.String(10), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'node_id'),
    )

    # ai_chat_sessions
    op.create_table(
        'ai_chat_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('context_type', sa.String(20), nullable=False),
        sa.Column('context_id', UUID(as_uuid=True), nullable=False),
        sa.Column('model_used', sa.String(50), nullable=True),
        sa.Column('message_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ai_chat_messages
    op.create_table(
        'ai_chat_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('ai_chat_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(10), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('token_count', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ai_cooldowns
    op.create_table(
        'ai_cooldowns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.String(100), nullable=True),
        sa.Column('cooldown_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # plan_quotas
    op.create_table(
        'plan_quotas',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('plan', sa.String(50), nullable=False, unique=True),
        sa.Column('monthly_uploads', sa.Integer, nullable=True),
        sa.Column('monthly_exams', sa.Integer, nullable=True),
        sa.Column('daily_ai_chats', sa.Integer, nullable=True),
        sa.Column('monthly_vision_pages', sa.Integer, nullable=True),
        sa.Column('max_file_size_mb', sa.Integer, nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('plan_quotas')
    op.drop_table('ai_cooldowns')
    op.drop_table('ai_chat_messages')
    op.drop_table('ai_chat_sessions')
    op.drop_table('node_mastery')
    op.drop_table('knowledge_nodes')
