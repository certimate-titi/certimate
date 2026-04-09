#!/bin/bash
# CertiMate Migration Squash Tool
#
# 將 001-040 的 40 個 migration 合併為單一 baseline migration。
# 新環境部署時可使用 baseline 取代逐步執行 40 個 migration。
#
# 前提：需要 pg_dump 或 Docker 內的 pg_dump
#
# 使用方式：
#   ./scripts/squash_migrations.sh
#
# 產出：
#   alembic/versions/000_baseline_schema.sql  — 完整 schema DDL
#   alembic/versions/000_baseline.py          — Alembic baseline migration

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_SQL="$PROJECT_DIR/alembic/versions/000_baseline_schema.sql"
OUTPUT_PY="$PROJECT_DIR/alembic/versions/000_baseline.py"

# 從 .env 或預設值取得 DB 連線
DB_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/certimate-api_dev}"

# 解析 DB 連線參數
DB_HOST=$(echo "$DB_URL" | sed -n 's|.*@\(.*\):\([0-9]*\)/.*|\1|p')
DB_PORT=$(echo "$DB_URL" | sed -n 's|.*@\(.*\):\([0-9]*\)/.*|\2|p')
DB_NAME=$(echo "$DB_URL" | sed -n 's|.*/\(.*\)|\1|p')
DB_USER=$(echo "$DB_URL" | sed -n 's|.*://\(.*\):.*@.*|\1|p')

echo "╔══���═════════════════════════════════════════════════════╗"
echo "║  CertiMate Migration Squash                           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "DB: $DB_HOST:$DB_PORT/$DB_NAME"

# 嘗試使用 pg_dump（本地或 Docker 內）
PG_DUMP=""
if command -v pg_dump &>/dev/null; then
    PG_DUMP="pg_dump"
elif docker ps | grep -q postgres; then
    CONTAINER=$(docker ps --filter "ancestor=postgres" --format "{{.ID}}" | head -1)
    if [ -n "$CONTAINER" ]; then
        PG_DUMP="docker exec $CONTAINER pg_dump"
        echo "使用 Docker container: $CONTAINER"
    fi
fi

if [ -z "$PG_DUMP" ]; then
    echo "❌ 找不到 pg_dump（本地或 Docker）"
    echo ""
    echo "替代方案："
    echo "  1. 安裝 postgresql: brew install postgresql@15"
    echo "  2. 或使用 Docker: docker run --rm postgres:15 pg_dump ..."
    exit 1
fi

echo ""
echo "📋 Step 1: 匯出 schema DDL..."
PGPASSWORD=postgres $PG_DUMP \
    -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --schema-only --no-owner --no-privileges --no-comments \
    --exclude-table=alembic_version \
    > "$OUTPUT_SQL"

LINE_COUNT=$(wc -l < "$OUTPUT_SQL")
echo "  ✓ 產出 $OUTPUT_SQL ($LINE_COUNT 行)"

echo ""
echo "📋 Step 2: 產生 Alembic baseline migration..."

cat > "$OUTPUT_PY" << 'PYEOF'
"""Baseline schema — squashed from migrations 001-040.

Revision ID: 000
Revises: (none — this IS the baseline)

使用方式：
  新環境部署時，執行此 migration 取代逐步執行 001-040。
  已有 001-040 的環境���需要執行此 migration。

  # 新環境：直接用 baseline
  alembic stamp 000
  alembic upgrade head

  # 或完整執行（等效但慢 40 倍）
  alembic upgrade head
"""
from pathlib import Path

from alembic import op

revision = "000"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_file = Path(__file__).parent / "000_baseline_schema.sql"
    if sql_file.exists():
        sql = sql_file.read_text()
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement and not statement.startswith("--"):
                op.execute(statement + ";")
    else:
        raise FileNotFoundError(
            f"Baseline SQL 檔案不存在: {sql_file}\n"
            "請先執行 scripts/squash_migrations.sh 產生 baseline"
        )


def downgrade() -> None:
    raise NotImplementedError("Baseline migration 不支援 downgrade")
PYEOF

echo "  ✓ 產出 $OUTPUT_PY"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  完成！                                                ║"
echo "║                                                        ║"
echo "║  新環境部署方式：                                       ║"
echo "║    alembic stamp 000                                   ║"
echo "║    alembic upgrade head                                ║"
echo "╚════════════════════════════════════════════════════════╝"
