"""Then step: AI 教練不應主動顯示對話視窗"""

from behave import then


@then('AI 教練不應主動顯示對話視窗')
def step_impl(context):
    data = context.last_response.json()
    assert data.get("coaching_triggered") is False, \
        f"Expected coaching_triggered=False, got: {data}"
