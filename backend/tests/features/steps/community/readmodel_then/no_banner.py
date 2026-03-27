"""Then step: 頁面不應包含「共同備考夥伴」橫幅區塊"""

from behave import then


@then('頁面不應包含「共同備考夥伴」橫幅區塊')
def step_impl(context):
    data = context.last_response.json()
    banner = data.get("banner")
    assert banner is None, f"Expected no banner, but got: {banner}"
