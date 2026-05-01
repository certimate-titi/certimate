"""Given PostgreSQL session 未呼叫 SET app.current_tenant_id."""

from behave import given
from sqlalchemy import text


@given("PostgreSQL session 未呼叫 SET app.current_tenant_id")
def step_impl(context):
    """確認 GUC app.current_tenant_id 未設定（空字串或未設）。

    PostgreSQL 的 current_setting() 在 GUC 未設定時若帶 missing_ok=true 回傳空字串。
    RLS NULLIF policy 必須能處理此情況，不能拋出 invalid input syntax for type uuid。
    """
    # RESET GUC（確保此 session 處於未設定狀態）
    try:
        context.db_session.execute(text("RESET app.current_tenant_id"))
        context.db_session.commit()
    except Exception:
        # 若 GUC 從未設定過，RESET 會靜默成功
        context.db_session.rollback()

    context.memo["guc_not_set"] = True
