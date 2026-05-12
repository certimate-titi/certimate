"""Then assertion — HTTP 狀態碼。"""

from behave import then


@then('回應狀態碼為 {code:d}')
def step_assert_http_status_code(context, code):
    response = context.last_response
    assert response.status_code == code, (
        f"預期 HTTP {code}，實際 {response.status_code}: {response.text[:200]}"
    )
