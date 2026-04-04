"""Then 回應應包含空狀態提示 — ReadModel Then"""

from behave import then


@then('回應應包含空狀態提示「{hint}」')
def step_impl(context, hint):
    response = context.last_response
    data = response.json()
    actual_hint = data.get("empty_hint", "")
    assert hint in str(actual_hint), \
        f"預期空狀態提示包含 '{hint}'，實際為 '{actual_hint}'"
