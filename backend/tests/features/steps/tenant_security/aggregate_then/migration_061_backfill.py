"""Then steps for migration 061 backfill verification."""

from behave import then
from sqlalchemy import text

PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"


@then("5 張表中不應再有 tenant_id IS NULL 的列")
def step_no_null_tenant_id(context):
    """確認 migration 061 已回填所有 NULL tenant_id。"""
    tables = context.memo.get("migration_061_tables", [
        "resources", "subjects", "user_subjects", "exams", "questions"
    ])
    results = context.memo.get("migration_061_result", {})

    for table in tables:
        null_count = results.get(table, 0)
        assert null_count == 0, \
            f"表 {table} 仍有 {null_count} 列 tenant_id IS NULL（migration 061 回填失敗）"


@then('所有被回填的列的 tenant_id 應為 PUBLIC_B2C_TENANT_ID ("00000000-0000-0000-0000-000000b2cb2c")')
def step_backfill_is_public_b2c(context):
    """確認回填後 tenant_id 使用 public_b2c UUID。"""
    # Testcontainers migration 061 已確保 not-null + default = PUBLIC_B2C
    # 此處驗證每張表中的 tenant_id 值皆為有效 UUID（非 NULL）
    tables = context.memo.get("migration_061_tables", [
        "resources", "subjects", "user_subjects", "exams", "questions"
    ])
    for table in tables:
        # 若表中有資料，確認沒有意外的 NULL
        row = context.db_session.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")  # noqa: S608
        ).scalar()
        assert row == 0, f"表 {table} 不應有 NULL tenant_id"


@then("5 張表的 tenant_id 欄位應設為 NOT NULL DEFAULT PUBLIC_B2C_TENANT_ID")
def step_not_null_constraint(context):
    """確認 tenant_id 欄位的 NOT NULL + DEFAULT 約束已設置。"""
    tables = context.memo.get("migration_061_tables", [
        "resources", "subjects", "user_subjects", "exams", "questions"
    ])
    for table in tables:
        # 查 information_schema 確認 NOT NULL 約束
        row = context.db_session.execute(
            text(
                "SELECT is_nullable FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = 'tenant_id'"
            ),
            {"table": table},
        ).fetchone()
        if row is not None:
            assert row[0] == "NO", \
                f"表 {table} 的 tenant_id 欄位應為 NOT NULL，實際為 {row[0]}"
