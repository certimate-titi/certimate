"""EDU subscription plan, trial support, and student role.

Revision ID: 028
Revises: 027
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = "028"
down_revision = "027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Extend subscription_plan enum with EDU ---
    op.execute("ALTER TYPE subscription_plan ADD VALUE IF NOT EXISTS 'EDU'")

    # --- Extend subscription_status enum with trial ---
    op.execute("ALTER TYPE subscription_status ADD VALUE IF NOT EXISTS 'trial'")

    # --- Extend user_role enum with student ---
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'student'")

    # --- Add trial & org fields to users ---
    op.add_column("users", sa.Column("trial_start_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("trial_end_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("has_used_trial", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("users", sa.Column("pre_trial_plan", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key("fk_users_org_id", "users", "institutions", ["org_id"], ["id"])

    # --- Seed EDU plan quota ---
    op.execute("""
        INSERT INTO plan_quotas (id, plan, daily_ai_chats, monthly_uploads, monthly_exams, monthly_vision_pages, max_file_size_mb)
        VALUES (gen_random_uuid(), 'EDU', 5, 0, 999999, 0, 0)
        ON CONFLICT (plan) DO NOTHING
    """)


def downgrade() -> None:
    op.drop_constraint("fk_users_org_id", "users", type_="foreignkey")
    op.drop_column("users", "org_id")
    op.drop_column("users", "pre_trial_plan")
    op.drop_column("users", "has_used_trial")
    op.drop_column("users", "trial_end_date")
    op.drop_column("users", "trial_start_date")
    # Note: PostgreSQL doesn't support removing enum values
