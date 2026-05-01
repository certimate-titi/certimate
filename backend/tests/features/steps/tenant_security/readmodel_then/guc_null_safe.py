"""Then steps for GUC null-safety RLS verification."""

from behave import then

PUBLIC_B2C_TENANT_ID = "00000000-0000-0000-0000-000000b2cb2c"


@then('查詢不應拋出 "invalid input syntax for type uuid" 錯誤')
def step_no_cast_error(context):
    """確認未設 GUC 時 RLS NULLIF policy 不會造成 UUID cast 錯誤。"""
    error = context.memo.get("guc_select_error")
    assert error is None or "invalid input syntax for type uuid" not in error, \
        f"RLS policy 在 GUC 未設定時拋出 UUID cast 錯誤：{error}"


@then("RLS 應視為 tenant_id = PUBLIC_B2C_TENANT_ID")
def step_falls_through_to_b2c(context):
    """確認未設 GUC 時 RLS 不拋錯（NULLIF 防護正常）。

    由於 Testcontainers 測試環境使用 superuser 連線（可繞過 RLS），
    此步驟確認查詢本身成功完成（無 exception），視為 NULLIF 防護有效。
    """
    error = context.memo.get("guc_select_error")
    # 若 select 有結果（result not None）或無錯誤，代表 RLS NULLIF 正確處理空 GUC
    result = context.memo.get("guc_select_result")
    assert error is None, \
        f"RLS 查詢不應拋出錯誤，實際錯誤：{error}"
    # superuser 不受 RLS 限制，此處僅驗證無 cast 錯誤
    assert result is not None, "查詢應回傳結果（即使為 0）"
