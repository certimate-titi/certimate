"""Then step: AI 教練（Certi）應主動顯示對話視窗"""

from behave import then


@then('AI 教練（Certi）應主動顯示對話視窗')
def step_impl(context):
    data = context.last_response.json()
    assert data.get("coaching_triggered") is True, \
        f"Expected coaching_triggered=True, got: {data}"
    assert data.get("coach_name") == "Certi", \
        f"Expected coach_name='Certi', got: {data.get('coach_name')}"
