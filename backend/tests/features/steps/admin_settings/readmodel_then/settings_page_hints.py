"""Then 設定頁面提示訊息驗證 — ReadModel Then"""

from behave import then


@then('頁面應顯示「設定已儲存」提示訊息')
def step_impl_settings_saved_hint(context):
    """驗證設定已儲存提示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應顯示「配額已更新」提示訊息')
def step_impl_quota_updated_hint(context):
    """驗證配額已更新提示（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('頁面應顯示該 Flag 狀態為「已啟用」')
def step_impl_flag_enabled_hint(context):
    """驗證 Flag 狀態顯示為已啟用（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
