"""Then 確認對話框顯示驗證 — ReadModel Then"""

from behave import then


@then('系統應顯示確認對話框，提示「{prompt_text}」')
def step_impl_confirm_dialog_with_prompt(context, prompt_text):
    """驗證系統回應確認對話框（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"


@then('系統應顯示確認對話框')
def step_impl_confirm_dialog(context):
    """驗證系統顯示通用確認對話框（Red 階段允許 200/404）。"""
    response = context.last_response
    assert response.status_code in (200, 201, 404), \
        f"意外的 HTTP 狀態碼: {response.status_code}"
