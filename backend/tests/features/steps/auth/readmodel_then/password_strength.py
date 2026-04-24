"""Then 密碼強度指示條 — 讀 memo（純前端狀態）。"""

from behave import then


@then('密碼強度指示條應顯示 "{level}"')
def step_impl(context, level):
    actual = context.memo.get("password_strength_label")
    assert actual == level, \
        f"密碼強度應為 '{level}'，實際為 '{actual}'"
