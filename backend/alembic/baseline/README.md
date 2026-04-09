# Alembic Baseline Schema

此目錄包含 squash 後的完整 schema DDL，供新環境快速部署使用。

## 使用方式

新環境不需要逐步執行 001-040 共 40 個 migration，可以直接：

```bash
# 1. 直接從 SQL 建立 schema
psql -h $DB_HOST -U $DB_USER -d $DB_NAME < alembic/baseline/schema_040.sql

# 2. 告訴 Alembic 當前版本是 040
.venv/bin/python -m alembic stamp 040

# 3. 之後的新 migration 正常執行
.venv/bin/python -m alembic upgrade head
```

## 更新 baseline

```bash
./scripts/squash_migrations.sh
```

## 檔案

- `schema_040.sql` — 48 tables, 509 columns, 106 indexes, 362 constraints
- 產生自 migrations 001-040 (2026-04-09)
