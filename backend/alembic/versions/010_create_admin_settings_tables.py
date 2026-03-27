"""010 create admin settings tables: ai_model_routings, system_announcements, feature_flags

Revision ID: 010
Revises: 009
Create Date: 2026-03-26
"""

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_model_routings",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("plan", sa.String(50), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("primary_model", sa.String(100), nullable=False),
        sa.Column("fallback_model", sa.String(100)),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "system_announcements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False, server_default="info"),
        sa.Column("display_mode", sa.String(50), nullable=False, server_default="banner"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("starts_at", sa.DateTime(timezone=True)),
        sa.Column("ends_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.UUID()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("flag_key", sa.String(100), nullable=False, unique=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("target_plans", sa.String(255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("feature_flags")
    op.drop_table("system_announcements")
    op.drop_table("ai_model_routings")
