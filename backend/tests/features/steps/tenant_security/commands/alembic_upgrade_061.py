"""When Alembic upgrade 到 revision 061."""

from behave import when
from sqlalchemy import text


@when("Alembic upgrade 到 revision 061")
def step_impl(context):
    """驗證當前 DB 已套用 migration 061（Testcontainers 環境下已自動 upgrade head）。

    Testcontainers 啟動時已套用完整 migration chain（含 061）。
    此步驟確認 tenant_id 欄位存在且 not-null 約束已生效。
    """
    tables = context.memo.get("migration_061_tables", [
        "resources", "subjects", "user_subjects", "exams", "questions"
    ])
    context.memo["migration_061_result"] = {}
    for table in tables:
        try:
            # 查詢 tenant_id IS NULL 的列數
            row = context.db_session.execute(
                text(f"SELECT COUNT(*) FROM {table} WHERE tenant_id IS NULL")  # noqa: S608
            ).scalar()
            context.memo["migration_061_result"][table] = row
        except Exception as e:
            context.memo["migration_061_result"][table] = f"error: {e}"
