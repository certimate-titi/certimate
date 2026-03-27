"""Create transactions, refunds, coupons tables.

Revision ID: 008
Revises: 007
Create Date: 2026-03-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merchant_trade_no", sa.String(20), unique=True, nullable=False),
        sa.Column("target_plan", sa.String(50), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payment_provider", sa.String(20), nullable=False, server_default="ecpay"),
        sa.Column("trade_no", sa.String(50)),
        sa.Column("payment_type", sa.String(50)),
        sa.Column("rtn_code", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_txn_user_id", "transactions", ["user_id"])
    op.create_index("idx_txn_status", "transactions", ["status"])

    op.create_table(
        "refunds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("refund_id", sa.String(100), unique=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_id", sa.String(100), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_refund_user_id", "refunds", ["user_id"])
    op.create_index("idx_refund_status", "refunds", ["status"])

    op.create_table(
        "coupons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(100), unique=True, nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("applicable_plans", sa.Text),
        sa.Column("max_uses", sa.Integer),
        sa.Column("max_uses_per_user", sa.Integer),
        sa.Column("used_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_coupon_code", "coupons", ["code"])
    op.create_index("idx_coupon_status", "coupons", ["status"])


def downgrade() -> None:
    op.drop_index("idx_coupon_status", "coupons")
    op.drop_index("idx_coupon_code", "coupons")
    op.drop_table("coupons")

    op.drop_index("idx_refund_status", "refunds")
    op.drop_index("idx_refund_user_id", "refunds")
    op.drop_table("refunds")

    op.drop_index("idx_txn_status", "transactions")
    op.drop_index("idx_txn_user_id", "transactions")
    op.drop_table("transactions")
