"""Then 操作失敗，狀態碼為 N — 驗證特定 HTTP 狀態碼。"""

from behave import then


@then('操作失敗，狀態碼為 {code:d}')
def step_impl(context, code):
    assert context.last_response is not None, "無 last_response"
    actual = context.last_response.status_code
    assert actual == code, f"預期狀態碼 {code}，實際 {actual}: {context.last_response.text}"
