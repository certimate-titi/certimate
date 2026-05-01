"""When 對 resources 表執行 SELECT（無 GUC 設定）."""

from behave import when
from sqlalchemy import text


@when("對 resources 表執行 SELECT")
def step_impl(context):
    """在未設定 app.current_tenant_id GUC 的情況下對 resources 執行 SELECT。

    驗證 RLS NULLIF policy 不會拋出 'invalid input syntax for type uuid' 錯誤。
    """
    context.memo["guc_select_error"] = None
    context.memo["guc_select_result"] = None

    try:
        result = context.db_session.execute(
            text("SELECT COUNT(*) FROM resources")
        ).scalar()
        context.memo["guc_select_result"] = result
    except Exception as e:
        context.memo["guc_select_error"] = str(e)
    finally:
        context.db_session.rollback()
