"""Then HTTP 狀態碼應為 — Read Model"""

from behave import then


@then('HTTP 狀態碼應為 {status_code:d}')
def step_impl(context, status_code):
    response = context.last_response
    assert response.status_code == status_code, (
        f"預期 HTTP {status_code}，實際 {response.status_code}: {response.text}"
    )
