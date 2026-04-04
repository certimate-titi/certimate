"""Then 回應應包含提示 — ReadModel Then"""

from behave import then


@then('回應應包含提示 "{hint}"')
def step_impl(context, hint):
    response = context.last_response
    data = response.json()

    # 提示可能在 hint、message、warning 欄位中
    actual_hint = (
        data.get("hint")
        or data.get("warning")
        or data.get("message")
        or ""
    )

    assert hint in str(actual_hint), (
        f"回應應包含提示 '{hint}'，但得到 '{actual_hint}'"
    )
