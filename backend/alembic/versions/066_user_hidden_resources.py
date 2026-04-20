"""Per-user soft-hide for platform/shared resources.

Revision ID: 066
Revises: 065

使用者對 platform / shared / institution 等非自己擁有的 Resource
點刪除時，不真的刪（會影響其他使用者），改寫一筆隱藏紀錄。
GET /resources 與知識地圖查詢會過濾掉這份紀錄。

Idempotent: IF NOT EXISTS。
"""

from alembic import op


revision = "066"
down_revision = "065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_hidden_resources (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
            hidden_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (user_id, resource_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_hidden_resources_user
            ON user_hidden_resources(user_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS user_hidden_resources")
