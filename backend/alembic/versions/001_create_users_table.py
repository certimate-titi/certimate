"""Create users table with all enum types.

Revision ID: 001
Revises:
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types
    subscription_plan = sa.Enum(
        'FREE', 'PRO_199', 'PRO_PLUS_399', 'ULTRA_1599',
        name='subscription_plan'
    )
    subscription_plan.create(op.get_bind(), checkfirst=True)

    subscription_status = sa.Enum(
        'active', 'cancelled', 'expired',
        name='subscription_status'
    )
    subscription_status.create(op.get_bind(), checkfirst=True)

    user_status = sa.Enum(
        'pending', 'active', 'suspended', 'cooling', 'deleted',
        name='user_status'
    )
    user_status.create(op.get_bind(), checkfirst=True)

    user_role = sa.Enum(
        'user', 'org_admin', 'admin', 'super_admin',
        name='user_role'
    )
    user_role.create(op.get_bind(), checkfirst=True)

    learning_preference = sa.Enum(
        'drill', 'concept', 'mixed',
        name='learning_preference'
    )
    learning_preference.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('auth_provider', sa.String(20), server_default='email'),
        sa.Column('password_hash', sa.Text(), nullable=True),
        sa.Column('subscription_plan', subscription_plan,
                  server_default='FREE'),
        sa.Column('subscription_status', subscription_status,
                  server_default='active'),
        sa.Column('next_billing_date', sa.DateTime(timezone=True),
                  nullable=True),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('role', user_role, server_default='user'),
        sa.Column('status', user_status, server_default='active'),
        sa.Column('onboarding_completed', sa.Boolean(),
                  server_default=sa.text('false')),
        sa.Column('daily_study_minutes', sa.Integer(),
                  server_default=sa.text('30')),
        sa.Column('learning_preference', learning_preference,
                  server_default='mixed'),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('education', sa.String(100), nullable=True),
        sa.Column('career', sa.String(100), nullable=True),
        sa.Column('agreed_to_terms', sa.Boolean(),
                  server_default=sa.text('false')),
        sa.Column('last_login_at', sa.DateTime(timezone=True),
                  nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('users')

    sa.Enum(name='learning_preference').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscription_status').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='subscription_plan').drop(op.get_bind(), checkfirst=True)
