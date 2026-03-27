"""Create users table with all enum types.

Revision ID: 001
Revises:
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        DO $$ BEGIN CREATE TYPE subscription_plan AS ENUM ('FREE', 'PRO', 'PRO_PLUS', 'ULTRA'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE subscription_status AS ENUM ('active', 'cancelled', 'expired'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE user_status AS ENUM ('pending', 'active', 'suspended', 'cooling', 'deleted'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE user_role AS ENUM ('user', 'org_admin', 'admin', 'super_admin'); EXCEPTION WHEN duplicate_object THEN null; END $$;
        DO $$ BEGIN CREATE TYPE learning_preference AS ENUM ('drill', 'concept', 'mixed'); EXCEPTION WHEN duplicate_object THEN null; END $$;
    """))

    op.execute(sa.text("""
        CREATE TABLE users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            display_name VARCHAR(100),
            avatar_url TEXT,
            auth_provider VARCHAR(20) DEFAULT 'email',
            password_hash TEXT,
            subscription_plan subscription_plan DEFAULT 'FREE',
            subscription_status subscription_status DEFAULT 'active',
            next_billing_date TIMESTAMPTZ,
            stripe_customer_id VARCHAR(100),
            role user_role DEFAULT 'user',
            status user_status DEFAULT 'active',
            onboarding_completed BOOLEAN DEFAULT false,
            daily_study_minutes INTEGER DEFAULT 30,
            learning_preference learning_preference DEFAULT 'mixed',
            age INTEGER,
            education VARCHAR(100),
            career VARCHAR(100),
            agreed_to_terms BOOLEAN DEFAULT false,
            last_login_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """))


def downgrade() -> None:
    op.execute(sa.text("DROP TABLE IF EXISTS users;"))
    op.execute(sa.text("""
        DROP TYPE IF EXISTS learning_preference;
        DROP TYPE IF EXISTS user_role;
        DROP TYPE IF EXISTS user_status;
        DROP TYPE IF EXISTS subscription_status;
        DROP TYPE IF EXISTS subscription_plan;
    """))
