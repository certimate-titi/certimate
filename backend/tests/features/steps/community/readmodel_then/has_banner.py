"""Then step: 頁面應顯示「共同備考夥伴」橫幅"""

from behave import then


@then('頁面應顯示「共同備考夥伴」橫幅')
def step_impl(context):
    data = context.last_response.json()
    banner = data.get("banner")
    assert banner is not None, "Expected banner to exist but it was None"
    assert banner.get("type") == "study_buddy", f"Expected study_buddy banner type, got: {banner.get('type')}"
