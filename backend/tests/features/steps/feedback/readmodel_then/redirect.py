"""Then 系統應導向至 "..." 頁面 / 登入頁面 / 登入成功後重新導向 — Readmodel Then"""

from behave import then


@then('系統應導向至 "{path}" 頁面')
def step_impl(context, path):
    # In API E2E context, we verify the redirect target stored in memo
    # For authenticated users hitting /feedback, a 2xx response means they're on the page
    redirect_target = context.memo.get("redirect_target")
    if redirect_target:
        assert redirect_target == path, \
            f"預期導向 '{path}'，實際導向 '{redirect_target}'"
    else:
        # Fallback: check response is successful (user reached the page)
        response = context.last_response
        assert response.status_code < 400, \
            f"預期成功存取 '{path}'，實際 HTTP {response.status_code}"


@then('系統應導向至登入頁面')
def step_impl(context):
    # For unauthenticated access, verify the API returned 401
    response = context.last_response
    assert response.status_code == 401, \
        f"預期 401（導向登入），實際 HTTP {response.status_code}"


@then('登入成功後應自動重新導向至 "{path}"')
def step_impl(context, path):
    # Verify the redirect_after_login memo was set correctly
    redirect_after = context.memo.get("redirect_after_login")
    assert redirect_after == path, \
        f"預期登入後導向 '{path}'，實際 '{redirect_after}'"
